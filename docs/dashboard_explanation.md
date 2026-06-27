\# Giải thích Dashboard Power BI — Dự án Olist Data Warehouse



\## 1. Bối cảnh dự án



Dashboard này được xây dựng cho dự án phân tích dữ liệu thương mại điện tử Olist. Dữ liệu được lấy từ PostgreSQL Data Warehouse sau quá trình ETL, bao gồm các bảng dimension, fact, snapshot và mart trong lớp `storage`.



Dashboard tập trung vào các nhóm phân tích chính:



\* Doanh thu

\* Đơn hàng

\* Tăng trưởng

\* Hủy đơn

\* Chi phí vận chuyển

\* Seller

\* Sản phẩm / ngành hàng

\* Khách hàng

\* Review và rủi ro review xấu



Dashboard gồm 6 trang, mỗi trang trả lời một nhóm câu hỏi kinh doanh khác nhau.



\---



\# Page 1 — Executive Overview



\## Mục tiêu



Trang này dùng để xem nhanh tình hình kinh doanh tổng quan của Olist.



\## Trang này trả lời các câu hỏi



\* Tổng doanh thu là bao nhiêu?

\* Có bao nhiêu đơn hàng?

\* Giá trị trung bình mỗi đơn hàng là bao nhiêu?

\* Phí vận chuyển chiếm bao nhiêu phần trăm so với doanh thu?

\* Tỷ lệ hủy đơn là bao nhiêu?

\* Tỷ lệ giao hàng thành công là bao nhiêu?

\* Điểm review trung bình là bao nhiêu?

\* Doanh thu và số lượng đơn hàng thay đổi như thế nào theo tháng?

\* Cơ cấu trạng thái đơn hàng gồm những nhóm nào?

\* Phân bố điểm review của khách hàng như thế nào?



\## Các biểu đồ chính



\* KPI Cards: Total Revenue, Order Count, Average Order Value, Freight Ratio, Cancellation Rate, Delivery Success Rate, Avg Review Score.

\* Biểu đồ doanh thu và số đơn theo tháng.

\* Biểu đồ trạng thái đơn hàng.

\* Biểu đồ tỷ lệ hủy đơn theo tháng.

\* Biểu đồ phân bố điểm review.



\## Ý nghĩa kinh doanh



Trang này giúp người xem nắm nhanh tình hình tổng thể của hệ thống Olist: doanh thu, đơn hàng, vận hành và trải nghiệm khách hàng.



\---



\# Page 2 — Revenue Growth



\## Mục tiêu



Trang này phân tích tăng trưởng doanh thu theo thời gian và xác định doanh thu tăng do số lượng đơn hàng hay do giá trị trung bình mỗi đơn hàng.



\## Trang này trả lời các câu hỏi



\* Doanh thu thay đổi như thế nào theo từng tháng?

\* Tốc độ tăng trưởng doanh thu theo tháng là bao nhiêu?

\* Doanh thu tăng là do số lượng đơn hàng tăng hay do Average Order Value tăng?

\* Tháng nào có tăng trưởng tốt?

\* Tháng nào có tăng trưởng giảm?

\* Average Order Value biến động như thế nào theo thời gian?



\## Các biểu đồ chính



\* KPI Cards: Total Revenue, Sales Growth Rate, Average Order Value, Order Count.

\* Line chart: Revenue Trend by Month.

\* Line chart: Monthly Sales Growth Rate.

\* Combo chart: Order Count vs Average Order Value.



\## Ý nghĩa kinh doanh



Trang này giúp giải thích nguyên nhân tăng trưởng doanh thu. Nếu doanh thu tăng cùng với số lượng đơn hàng, tăng trưởng chủ yếu đến từ volume. Nếu doanh thu tăng nhưng số lượng đơn không tăng mạnh, tăng trưởng có thể đến từ giá trị đơn hàng cao hơn.



\---



\# Page 3 — Cancellation \& Freight Risk



\## Mục tiêu



Trang này phân tích rủi ro vận hành liên quan đến hủy đơn và chi phí vận chuyển.



\## Trang này trả lời các câu hỏi



\* Tỷ lệ hủy đơn là bao nhiêu?

\* Doanh thu ước tính bị mất do đơn hủy là bao nhiêu?

\* Tỷ lệ giao hàng thành công là bao nhiêu?

\* Tổng phí vận chuyển là bao nhiêu?

\* Phí vận chuyển chiếm bao nhiêu phần trăm so với doanh thu?

\* Có đơn hàng nào có phí vận chuyển cao bất thường so với giá trị đơn hàng không?

\* Tỷ lệ hủy đơn thay đổi như thế nào theo tháng?

\* Freight Ratio thay đổi như thế nào theo tháng?

\* Trạng thái đơn hàng phân bố ra sao?



\## Các biểu đồ chính



\* KPI Cards nhóm Order Risk: Cancellation Rate, Lost Revenue Proxy, Delivery Success Rate.

\* KPI Cards nhóm Delivery Cost: Total Freight, Freight Ratio, Avg Waiting Day.

\* Scatter chart: Freight Value vs Order Value.

\* Line chart: Cancellation Rate by Month.

\* Area/Line chart: Freight Ratio by Month.

\* Bar chart: Order Count by Status.



\## Ý nghĩa kinh doanh



Trang này giúp phát hiện các vấn đề vận hành như đơn hàng bị hủy, chi phí vận chuyển cao và các đơn hàng có freight bất thường so với giá trị đơn hàng. Đây là cơ sở để tối ưu logistics và giảm rủi ro thất thoát doanh thu.



\---



\# Page 4 — Seller Performance



\## Mục tiêu



Trang này phân tích hiệu quả hoạt động của seller và nhận diện seller có đóng góp cao hoặc rủi ro cao.



\## Trang này trả lời các câu hỏi



\* Seller nào tạo ra doanh thu cao nhất?

\* Seller nào có số lượng đơn hàng lớn nhất?

\* Seller có Average Order Value cao hay thấp?

\* Seller nào có tỷ lệ hủy đơn cao?

\* Seller nào vừa có doanh thu cao vừa có rủi ro vận hành cao?

\* Seller nào có điểm review trung bình tốt?

\* Nên ưu tiên theo dõi seller nào?



\## Các biểu đồ chính



\* Bar chart: Top Sellers by Revenue.

\* KPI Cards: Seller Revenue, Seller Orders, Seller AOV, Seller Cancellation Rate, Seller Avg Review.

\* Scatter chart: Seller Revenue vs Cancellation Risk.

\* Table: Seller Scorecard.



\## Ý nghĩa kinh doanh



Trang này giúp nhóm kinh doanh và vận hành nhận diện seller chủ lực, seller có hiệu quả tốt và seller cần kiểm tra do tỷ lệ hủy đơn hoặc rủi ro vận hành cao.



\---



\# Page 5 — Category Portfolio Explorer



\## Mục tiêu



Trang này phân tích danh mục sản phẩm và ngành hàng, từ đó xác định category/product nào đóng góp doanh thu và tốc độ bán tốt nhất.



\## Trang này trả lời các câu hỏi



\* Category nào đóng góp doanh thu lớn nhất?

\* Product nào nằm trong nhóm category có doanh thu cao?

\* Doanh thu theo category thay đổi thứ hạng như thế nào qua thời gian?

\* Product nào có tốc độ bán nhanh?

\* Category nào đang là nhóm sản phẩm chủ lực?

\* Product nào có doanh thu tốt nhưng review chưa cao?

\* Product nào nên được ưu tiên trong phân tích danh mục?



\## Các biểu đồ chính



\* KPI Cards: Product Revenue, Product Items Sold, Product Sales Velocity, Product Avg Review.

\* Decomposition Tree: Revenue Decomposition by Category and Product.

\* Ribbon chart: Category Revenue Rank by Month.

\* Table: Top Fast-Moving Products.



\## Ý nghĩa kinh doanh



Trang này hỗ trợ phân tích danh mục sản phẩm. Decomposition Tree giúp bóc tách doanh thu từ tổng doanh thu xuống category và product. Ribbon chart giúp xem category nào thay đổi thứ hạng doanh thu qua các tháng. Bảng Top Fast-Moving Products giúp nhận diện sản phẩm bán nhanh.



\---



\# Page 6 — Customer \& Review Risk



\## Mục tiêu



Trang này phân tích giá trị khách hàng và rủi ro review xấu, đặc biệt liên quan đến thời gian chờ và tỷ lệ phí vận chuyển.



\## Trang này trả lời các câu hỏi



\* Có bao nhiêu khách hàng duy nhất?

\* Tổng chi tiêu của khách hàng là bao nhiêu?

\* Nhóm khách hàng nào có giá trị chi tiêu cao?

\* Khách hàng mua nhiều có chi tiêu cao hơn không?

\* Tỷ lệ review xấu là bao nhiêu?

\* Điểm review trung bình là bao nhiêu?

\* Thời gian chờ giao hàng có liên quan đến review score không?

\* Nhóm đơn hàng nào có rủi ro review xấu cao?

\* Freight Ratio và Waiting Day kết hợp như thế nào để tạo rủi ro review xấu?



\## Các biểu đồ chính



\* KPI Cards nhóm Customer Value: Customer Count, Customer Total Spend.

\* KPI Cards nhóm Review Risk: Bad Review Rate, Avg Review Score.

\* Scatter chart: Customer Spend vs Order Frequency.

\* Scatter chart: Waiting Day vs Review Score.

\* Matrix heatmap: Bad Review Rate by Waiting Time and Freight Ratio.



\## Ý nghĩa kinh doanh



Trang này giúp kết nối hai góc nhìn: giá trị khách hàng và rủi ro trải nghiệm. Scatter chart giúp nhận diện khách hàng có chi tiêu cao hoặc đơn hàng có thời gian chờ lâu nhưng review thấp. Heatmap giúp xác định nhóm đơn hàng có khả năng tạo review xấu cao, hỗ trợ cải thiện trải nghiệm khách hàng.



\---



\# Tổng kết thiết kế Dashboard



Dashboard được thiết kế theo 6 phong cách phân tích khác nhau để tránh trùng lặp về bố cục:



| Trang                                | Phong cách phân tích        | Mục đích                                          |

| ------------------------------------ | --------------------------- | ------------------------------------------------- |

| Page 1 — Executive Overview          | Tổng quan KPI               | Theo dõi tình hình kinh doanh chung               |

| Page 2 — Revenue Growth              | Phân tích chuỗi thời gian   | Giải thích tăng trưởng doanh thu                  |

| Page 3 — Cancellation \& Freight Risk | Phân tích rủi ro vận hành   | Kiểm tra hủy đơn và chi phí vận chuyển            |

| Page 4 — Seller Performance          | Leaderboard và risk map     | So sánh hiệu quả seller                           |

| Page 5 — Category Portfolio Explorer | Phân tích khám phá danh mục | Bóc tách doanh thu category/product               |

| Page 6 — Customer \& Review Risk      | Diagnostic dashboard        | Phân tích giá trị khách hàng và rủi ro review xấu |



Dashboard chỉ sử dụng các bảng hiện có trong data warehouse, bao gồm fact table, dimension table, snapshot table và mart. Không tự tạo dữ liệu ngoài hoặc giả định thêm cột không có trong warehouse, ngoại trừ các measure DAX phục vụ phân tích trong Power BI.



