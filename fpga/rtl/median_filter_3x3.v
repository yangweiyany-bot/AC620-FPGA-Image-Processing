module median_filter_3x3
(
    input  wire       clk,
    input  wire       rst_n,

    input  wire [7:0] pixel_in,
    input  wire       pixel_valid,

    output reg  [7:0] pixel_out,
    output reg        pixel_out_valid
);

    // 保存前两行像素
    reg [7:0] line1 [0:255];
    reg [7:0] line2 [0:255];

    // 当前坐标
    reg [7:0] col;
    reg [7:0] row;

    // 当前3×3窗口
    reg [7:0] p00, p01;
    reg [7:0] p10, p11;

    integer i;

    // --------------------------------------------------------
    // 9个数求中值
    // --------------------------------------------------------
    function [7:0] median9;

        input [7:0] a0;
        input [7:0] a1;
        input [7:0] a2;
        input [7:0] a3;
        input [7:0] a4;
        input [7:0] a5;
        input [7:0] a6;
        input [7:0] a7;
        input [7:0] a8;

        reg [7:0] a [0:8];
        reg [7:0] temp;

        integer x;
        integer y;

        begin

            a[0] = a0;
            a[1] = a1;
            a[2] = a2;
            a[3] = a3;
            a[4] = a4;
            a[5] = a5;
            a[6] = a6;
            a[7] = a7;
            a[8] = a8;

            // 简单排序
            for (x = 0; x < 8; x = x + 1) begin

                for (y = x + 1; y < 9; y = y + 1) begin

                    if (a[y] < a[x]) begin

                        temp = a[x];
                        a[x] = a[y];
                        a[y] = temp;

                    end

                end

            end

            // 排序后的第5个数
            median9 = a[4];

        end

    endfunction


    // --------------------------------------------------------
    // 3×3滑动窗口
    // --------------------------------------------------------

    always @(posedge clk or negedge rst_n) begin

        if (!rst_n) begin

            col <= 0;
            row <= 0;

            p00 <= 0;
            p01 <= 0;

            p10 <= 0;
            p11 <= 0;

            pixel_out <= 0;
            pixel_out_valid <= 0;

        end else begin

            pixel_out_valid <= 0;

            if (pixel_valid) begin

                // 当至少已经接收到3行、3列时
                if ((row >= 2) && (col >= 2)) begin

                    pixel_out <= median9(
                        p00,
                        p01,
                        line2[col],

                        p10,
                        p11,
                        line1[col],

                        line1[col-2],
                        line1[col-1],
                        pixel_in
                    );

                    pixel_out_valid <= 1'b1;

                end


                // 更新窗口
                p00 <= p01;
                p01 <= line2[col];

                p10 <= p11;
                p11 <= line1[col];


                // 更新行缓存
                line2[col] <= line1[col];
                line1[col] <= pixel_in;


                // 更新坐标
                if (col == 255) begin

                    col <= 0;

                    if (row == 255)
                        row <= 0;
                    else
                        row <= row + 1'b1;

                end else begin

                    col <= col + 1'b1;

                end

            end

        end

    end

endmodule