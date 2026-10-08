module mean_filter_3x3
(
    input  wire       clk,
    input  wire       rst_n,

    input  wire [7:0] pixel_in,
    input  wire       pixel_valid,

    output reg  [7:0] pixel_out,
    output reg        pixel_out_valid
);

    // --------------------------------------------------
    // 两行缓存
    //
    // line1[col]：上一行
    // line2[col]：上两行
    // --------------------------------------------------
    reg [7:0] line1 [0:255];
    reg [7:0] line2 [0:255];

    reg [7:0] col;
    reg [7:0] row;

    // 保存每一行最近两个像素
    reg [7:0] top_1, top_2;
    reg [7:0] mid_1, mid_2;
    reg [7:0] bot_1, bot_2;

    reg [11:0] sum;

    integer i;

    always @(posedge clk or negedge rst_n) begin

        if (!rst_n) begin

            col <= 0;
            row <= 0;

            pixel_out       <= 0;
            pixel_out_valid <= 0;

            top_1 <= 0;
            top_2 <= 0;

            mid_1 <= 0;
            mid_2 <= 0;

            bot_1 <= 0;
            bot_2 <= 0;

            sum <= 0;

            for (i = 0; i < 256; i = i + 1) begin
                line1[i] <= 0;
                line2[i] <= 0;
            end

        end else begin

            pixel_out_valid <= 0;

            if (pixel_valid) begin

                // --------------------------------------
                // 当前时刻能够得到：
                //
                // top_2 top_1 line2[col]
                // mid_2 mid_1 line1[col]
                // bot_2 bot_1 pixel_in
                // --------------------------------------

                if ((row >= 2) && (col >= 2)) begin

                    sum <=
                        top_2 + top_1 + line2[col] +
                        mid_2 + mid_1 + line1[col] +
                        bot_2 + bot_1 + pixel_in;

                    pixel_out <=
                        (top_2 + top_1 + line2[col] +
                         mid_2 + mid_1 + line1[col] +
                         bot_2 + bot_1 + pixel_in) / 9;

                    pixel_out_valid <= 1'b1;

                end

                // --------------------------------------
                // 更新横向移位寄存器
                // --------------------------------------

                top_2 <= top_1;
                top_1 <= line2[col];

                mid_2 <= mid_1;
                mid_1 <= line1[col];

                bot_2 <= bot_1;
                bot_1 <= pixel_in;

                // --------------------------------------
                // 更新两行缓存
                // --------------------------------------

                line2[col] <= line1[col];
                line1[col] <= pixel_in;

                // --------------------------------------
                // 更新行列坐标
                // --------------------------------------

                if (col == 255) begin

                    col <= 0;

                    // 非常重要：
                    // 换行以后，横向历史必须清零
                    top_1 <= 0;
                    top_2 <= 0;

                    mid_1 <= 0;
                    mid_2 <= 0;

                    bot_1 <= 0;
                    bot_2 <= 0;

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