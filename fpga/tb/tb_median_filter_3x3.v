`timescale 1ns/1ps

module tb_median_filter_3x3;

    reg clk;
    reg rst_n;

    reg [7:0] pixel_in;
    reg       pixel_valid;

    wire [7:0] pixel_out;
    wire       pixel_out_valid;

    // ========================================================
    // 实例化中值滤波模块
    // ========================================================

    median_filter_3x3 dut (
        .clk            (clk),
        .rst_n          (rst_n),
        .pixel_in       (pixel_in),
        .pixel_valid    (pixel_valid),
        .pixel_out      (pixel_out),
        .pixel_out_valid(pixel_out_valid)
    );


    // ========================================================
    // 50 MHz 时钟
    // ========================================================

    initial begin
        clk = 0;
        forever #10 clk = ~clk;
    end


    // ========================================================
    // 发送一个像素
    // ========================================================

    task send_pixel;

        input [7:0] data;

        begin

            @(negedge clk);

            pixel_in    = data;
            pixel_valid = 1'b1;

            @(negedge clk);

            pixel_valid = 1'b0;

        end

    endtask


    // ========================================================
    // 测试
    // ========================================================

    initial begin

        rst_n       = 0;
        pixel_in    = 0;
        pixel_valid = 0;

        #100;

        rst_n = 1;

        #100;


        // ----------------------------------------------------
        // 发送完整的 3×3 图像
        //
        // 10   20   30
        // 40  255   60
        // 70   80   90
        //
        // 排序：
        // 10 20 30 40 60 70 80 90 255
        //
        // 中值应该 = 60
        // ----------------------------------------------------

        send_pixel(10);
        send_pixel(20);
        send_pixel(30);

        // 补齐第一行剩余253个像素
        repeat(253)
            send_pixel(0);


        send_pixel(40);
        send_pixel(255);
        send_pixel(60);

        // 补齐第二行
        repeat(253)
            send_pixel(0);


        send_pixel(70);
        send_pixel(80);
        send_pixel(90);


        #500;


        $display("==============================");
        $display("MEDIAN FILTER TEST FINISHED");
        $display("==============================");

        $stop;

    end


    // ========================================================
    // 监视有效输出
    // ========================================================

    always @(posedge clk) begin

        if (pixel_out_valid) begin

            $display(
                "Median output = %d",
                pixel_out
            );

            if (pixel_out == 60)
                $display("MEDIAN_FILTER_PASS");
            else
                $display("MEDIAN_FILTER_FAIL");

        end

    end

endmodule