module ac620_uart_loopback_top
(
    input  wire       clk,
    input  wire       rst_n,
    input  wire       uart_rx,
    output wire       uart_tx,
    output wire       led
);

    localparam integer CLK_FREQ  = 50_000_000;
    localparam integer BAUD_RATE = 115_200;

    // ============================================================
    // UART RX
    // ============================================================

    wire [7:0] rx_data;
    wire       rx_valid;

    uart_rx #(
        .CLK_FREQ (CLK_FREQ),
        .BAUD_RATE(BAUD_RATE)
    ) u_uart_rx (
        .clk       (clk),
        .rst_n     (rst_n),
        .rx        (uart_rx),
        .data_out  (rx_data),
        .data_valid(rx_valid)
    );


    // ============================================================
    // 通信协议
    //
    // AA 55 00 -> 选择 3x3 均值滤波
    // AA 55 01 -> 选择 3x3 中值滤波
    //
    // 命令后发送：
    // 256 x 256 = 65536 个灰度像素
    //
    // 收满 65536 个像素以后：
    // 自动退出 image_mode
    // 等待下一条 AA 55 XX 命令
    // ============================================================

    reg [1:0]  cmd_state;
    reg        image_mode;
    reg        filter_select;
    reg [16:0] pixel_count;

    // filter_select:
    // 0 = mean filter
    // 1 = median filter

    wire pixel_valid;

    assign pixel_valid = rx_valid && image_mode;


    // ============================================================
    // 命令解析 + 图像像素计数
    // ============================================================

    always @(posedge clk or negedge rst_n) begin

        if (!rst_n) begin

            cmd_state     <= 2'd0;
            image_mode    <= 1'b0;
            filter_select <= 1'b0;
            pixel_count   <= 17'd0;

        end else begin

            // ----------------------------------------------------
            // 当前处于命令接收模式
            // ----------------------------------------------------

            if (rx_valid && !image_mode) begin

                case (cmd_state)

                    // 等待 AA
                    2'd0: begin

                        if (rx_data == 8'hAA)
                            cmd_state <= 2'd1;
                        else
                            cmd_state <= 2'd0;

                    end


                    // 等待 55
                    2'd1: begin

                        if (rx_data == 8'h55)
                            cmd_state <= 2'd2;
                        else
                            cmd_state <= 2'd0;

                    end


                    // 等待滤波模式
                    2'd2: begin

                        // ------------------------------
                        // 00：均值滤波
                        // ------------------------------

                        if (rx_data == 8'h00) begin

                            filter_select <= 1'b0;
                            image_mode    <= 1'b1;
                            pixel_count   <= 17'd0;

                        end

                        // ------------------------------
                        // 01：中值滤波
                        // ------------------------------

                        else if (rx_data == 8'h01) begin

                            filter_select <= 1'b1;
                            image_mode    <= 1'b1;
                            pixel_count   <= 17'd0;

                        end

                        cmd_state <= 2'd0;

                    end


                    default: begin

                        cmd_state <= 2'd0;

                    end

                endcase
            end


            // ----------------------------------------------------
            // 当前处于图像接收模式
            //
            // 一共接收：
            // 256 x 256 = 65536 pixels
            //
            // pixel_count:
            // 0 ~ 65535
            // ----------------------------------------------------

            else if (rx_valid && image_mode) begin

                if (pixel_count == 17'd65535) begin

                    // 已经收到最后一个像素
                    pixel_count <= 17'd0;

                    // 本张图片结束
                    // 回到命令接收状态
                    image_mode <= 1'b0;

                end else begin

                    pixel_count <= pixel_count + 1'b1;

                end

            end

        end

    end


    // ============================================================
    // 3x3 均值滤波器
    // ============================================================

    wire [7:0] mean_data;
    wire       mean_valid;

    mean_filter_3x3 u_mean_filter (
        .clk            (clk),
        .rst_n          (rst_n),

        .pixel_in       (rx_data),
        .pixel_valid    (pixel_valid),

        .pixel_out      (mean_data),
        .pixel_out_valid(mean_valid)
    );


    // ============================================================
    // 3x3 中值滤波器
    // ============================================================

    wire [7:0] median_data;
    wire       median_valid;

    median_filter_3x3 u_median_filter (
        .clk            (clk),
        .rst_n          (rst_n),

        .pixel_in       (rx_data),
        .pixel_valid    (pixel_valid),

        .pixel_out      (median_data),
        .pixel_out_valid(median_valid)
    );


    // ============================================================
    // 根据 Python 发来的命令选择滤波结果
    // ============================================================

    wire [7:0] filter_data;
    wire       filter_valid;

    assign filter_data =
        (filter_select == 1'b0)
        ? mean_data
        : median_data;

    assign filter_valid =
        (filter_select == 1'b0)
        ? mean_valid
        : median_valid;


    // ============================================================
    // UART TX
    // ============================================================

    reg  [7:0] pending_data;
    reg        pending_valid;

    wire       tx_ready;
    wire       tx_start;

    assign tx_start = pending_valid && tx_ready;


    uart_tx #(
        .CLK_FREQ (CLK_FREQ),
        .BAUD_RATE(BAUD_RATE)
    ) u_uart_tx (
        .clk       (clk),
        .rst_n     (rst_n),
        .data_in   (pending_data),
        .data_valid(tx_start),
        .tx        (uart_tx),
        .ready     (tx_ready)
    );


    // ============================================================
    // 保存滤波结果，并通过 UART 返回电脑
    // ============================================================

    always @(posedge clk or negedge rst_n) begin

        if (!rst_n) begin

            pending_data  <= 8'h00;
            pending_valid <= 1'b0;

        end else begin

            // 滤波器产生一个新的有效像素
            if (filter_valid) begin

                pending_data  <= filter_data;
                pending_valid <= 1'b1;

            end

            // UART 已经开始发送
            else if (tx_start) begin

                pending_valid <= 1'b0;

            end

        end

    end


    // ============================================================
    // LED 活动指示
    //
    // LED0 为低电平点亮
    // 每收到 UART 数据以后保持亮约 1 秒
    // ============================================================

    reg [25:0] activity_count;

    always @(posedge clk or negedge rst_n) begin

        if (!rst_n) begin

            activity_count <= 26'd0;

        end else if (rx_valid) begin

            activity_count <= 26'd50_000_000;

        end else if (activity_count != 0) begin

            activity_count <= activity_count - 1'b1;

        end

    end


    assign led =
        (activity_count != 0)
        ? 1'b0
        : 1'b1;


endmodule