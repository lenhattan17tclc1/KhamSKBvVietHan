# Python Development Skill

## Mục đích

Skill này áp dụng cho mọi thay đổi, sửa lỗi, phát triển tính năng và bảo trì trong các dự án Python.

Mục tiêu:

> **Ưu tiên tính đúng đắn của dữ liệu và nghiệp vụ, bảo toàn hành vi hiện tại, thay đổi code ở mức tối thiểu, tái sử dụng những gì đã có và luôn kiểm tra lại sau khi thay đổi.**

Skill này được thiết kế để dùng cho nhiều loại project Python: desktop app, web app, API, automation, data processing, CLI, service, tool nội bộ hoặc hệ thống có database.

---

# 1. ƯU TIÊN PHÂN TÍCH TRƯỚC KHI SỬA

Không bắt đầu sửa code ngay khi nhận yêu cầu.

Trước tiên phải:

1. Hiểu yêu cầu thực tế.
2. Xác định code liên quan.
3. Tìm function/class/module đang xử lý chức năng đó.
4. Tìm nơi gọi function/class đó.
5. Kiểm tra dữ liệu đầu vào và đầu ra.
6. Kiểm tra các dependency liên quan.
7. Kiểm tra test hiện có.
8. Xác định phạm vi ảnh hưởng.

Nếu chưa hiểu nguyên nhân hoặc luồng xử lý hiện tại thì **không nên sửa theo phỏng đoán**.

Ưu tiên:

```text
Understand
→ Locate
→ Trace
→ Identify root cause
→ Plan minimal change
→ Implement
→ Test
→ Verify
```

---

# 2. DATA CORRECTNESS FIRST

Nếu phát hiện dữ liệu sai, dữ liệu mất, dữ liệu không đồng nhất hoặc kết quả nghiệp vụ sai:

> **Ưu tiên xác định và sửa nguyên nhân dữ liệu trước khi làm các thay đổi khác.**

Không dùng workaround để che lỗi dữ liệu.

Không được:

```text
Dữ liệu sai
→ thêm điều kiện để che lỗi
→ đổi UI để không nhìn thấy lỗi
→ tiếp tục phát triển tính năng khác
```

Ưu tiên:

```text
Identify
→ Verify
→ Find root cause
→ Determine affected scope
→ Correct
→ Verify again
```

Nếu chưa xác định được nguyên nhân thì phải nói rõ chưa đủ thông tin và kiểm tra thêm, không tự suy đoán.

---

# 3. KHÔNG SỬA NHIỀU HƠN MỨC CẦN THIẾT

Một yêu cầu nhỏ không được trở thành lý do để thay đổi toàn bộ hệ thống.

Ví dụ:

```text
Yêu cầu:
Sửa lỗi format ngày

Không nên:
→ refactor toàn bộ module xử lý ngày
→ thay database layer
→ đổi framework
→ đổi cấu trúc project
```

Nguyên tắc:

> **Fix the smallest possible surface area.**

Trước khi sửa, xác định:

```text
What must change?
What must NOT change?
```

Nếu có thể giải quyết bằng 5 dòng code thì không nên thay 200 dòng.

---

# 4. KHÔNG TỰ Ý THAY ĐỔI CẤU TRÚC SOURCE

Không tự ý:

- đổi tên folder
- đổi tên module
- đổi tên function
- đổi tên class
- chuyển file
- đổi architecture
- đổi framework
- đổi database structure
- đổi API contract
- đổi config structure

trừ khi yêu cầu thực sự cần.

Nếu cần thay đổi cấu trúc:

1. Xác định lý do.
2. Xác định phạm vi ảnh hưởng.
3. Kiểm tra toàn bộ nơi đang sử dụng.
4. Kiểm tra import/reference.
5. Kiểm tra test.
6. Thực hiện thay đổi có kiểm soát.
7. Test toàn bộ phần bị ảnh hưởng.

Không refactor chỉ vì "có thể viết đẹp hơn".

---

# 5. ƯU TIÊN TÁI SỬ DỤNG CODE HIỆN CÓ

Trước khi tạo function/class/module mới:

> **Phải tìm xem project đã có chức năng tương tự hay chưa.**

Tìm:

- function tương tự
- class tương tự
- utility/helper
- validator
- parser
- database function
- API service
- UI component
- config loader
- logging function
- error handler

Nếu đã có logic phù hợp:

```text
Reuse existing function
```

thay vì:

```text
Create duplicate function
```

Không tạo nhiều implementation cho cùng một business logic.

---

# 6. KHÔNG DUPLICATE BUSINESS LOGIC

Nếu cùng một quy tắc xuất hiện ở nhiều nơi:

```text
UI
API
Service
Database
Import
Export
```

phải xác định nơi nào đang là source of truth.

Không copy cùng một logic sang nhiều file nếu có thể dùng chung.

Ví dụ không nên:

```python
def validate_user_a():
    ...

def validate_user_b():
    ...
```

nếu cả hai thực hiện cùng một business rule.

Ưu tiên:

```python
def validate_user():
    ...
```

và tái sử dụng.

Tuy nhiên, không refactor lớn chỉ để loại bỏ một duplication nhỏ nếu việc đó làm tăng phạm vi thay đổi không cần thiết.

---

# 7. BẢO TOÀN BEHAVIOR HIỆN TẠI

Khi thêm hoặc sửa một chức năng:

> Chỉ thay đổi behavior được yêu cầu.

Các behavior khác phải tiếp tục hoạt động như trước.

Đặc biệt chú ý:

- API
- UI
- database
- file format
- config
- import/export
- authentication
- permission
- logging
- background task
- scheduled task
- external integration

Không được coi việc code chạy không báo lỗi là đủ.

---

# 8. BUSINESS RULE PRIORITY

Nếu có xung đột giữa:

```text
User request
Existing code
UI behavior
API behavior
Database behavior
Configuration
Documentation
Existing business rule
```

không được tự ý chọn một bên.

Phải:

1. Xác định behavior thực tế.
2. Xác định business rule.
3. Kiểm tra nơi rule đang được implement.
4. Xác định tác động của thay đổi.
5. Nếu còn mâu thuẫn, hỏi lại hoặc nêu rõ giả định.

Không tự tạo business rule mới chỉ vì implementation hiện tại chưa rõ ràng.

---

# 9. DATABASE & DATA INTEGRITY

Nếu project có database, phải coi database là một phần quan trọng của hệ thống.

Trước khi thay đổi:

- schema
- column
- type
- constraint
- relationship
- migration
- query
- transaction

phải kiểm tra code đang sử dụng chúng.

Không tự ý:

- xóa column
- đổi type
- đổi primary key
- đổi foreign key
- xóa record
- reset database

nếu chưa đánh giá ảnh hưởng.

Nếu thao tác có nguy cơ làm mất dữ liệu:

> Phải ưu tiên backup hoặc có phương án rollback trước khi thực hiện.

---

# 10. DELETE POLICY

Không được xóa dữ liệu chỉ để làm code hoặc database "sạch hơn".

Trước khi delete phải xác định:

```text
Có record khác reference không?
Có history không?
Có log không?
Có report phụ thuộc không?
Có cần giữ dữ liệu cũ không?
Có thể dùng soft delete không?
```

Nếu hệ thống đã có delete policy thì phải tuân thủ policy hiện tại.

Không hard delete chỉ vì thao tác đó đơn giản hơn.

---

# 11. IMPORT / EXPORT

Nếu project có import/export:

Import phải ưu tiên:

```text
Validate
→ Detect invalid data
→ Detect duplicate
→ Preview/Report
→ Confirm
→ Write data
→ Verify
```

Cần kiểm tra:

- missing required field
- duplicate
- invalid type
- invalid date
- invalid number
- unexpected format
- encoding
- empty value
- unexpected column
- invalid reference

Export phải đảm bảo:

- đúng dữ liệu
- đúng filter
- đúng format
- không bỏ sót record
- không làm thay đổi dữ liệu gốc
- không có side effect ngoài mong muốn

---

# 12. CONFIGURATION

Trước khi thay đổi config:

- tìm file config hiện tại
- tìm default config
- tìm nơi load config
- tìm nơi validate config
- kiểm tra backward compatibility

Không tự ý đổi format config nếu chưa kiểm tra dữ liệu config cũ.

Nếu thêm config mới:

> Ưu tiên default value an toàn để project cũ vẫn chạy được.

---

# 13. ERROR HANDLING

Không che lỗi bằng:

```python
except:
    pass
```

hoặc các workaround tương tự.

Error handling phải:

- bắt đúng loại exception khi có thể
- giữ lại thông tin lỗi
- log lỗi nếu cần
- không làm mất dữ liệu
- không làm chương trình tiếp tục trong trạng thái không hợp lệ

Không dùng exception handling để che nguyên nhân gốc.

---

# 14. LOGGING

Nếu project đã có logging system:

> Phải sử dụng logging hiện tại thay vì tạo logging riêng.

Log những thông tin cần thiết để debug:

```text
What happened
Where
When
Relevant identifier
Error
Context
```

Không log:

- password
- token
- secret key
- private key
- thông tin nhạy cảm không cần thiết

---

# 15. SECURITY

Không tự ý làm giảm mức bảo mật để sửa lỗi nhanh.

Đặc biệt chú ý:

- password
- API key
- token
- secret
- database credential
- file permission
- authentication
- authorization
- input validation
- path traversal
- command injection
- SQL injection

Không hard-code secret vào source code.

Nếu project đã có cơ chế bảo mật thì ưu tiên sử dụng cơ chế đó.

---

# 16. UI CHANGE

Nếu sửa UI:

> Chỉ thay đổi phần UI liên quan đến yêu cầu.

Không tự ý thay đổi:

- layout toàn bộ app
- theme
- màu sắc
- font
- navigation
- component structure

trừ khi được yêu cầu.

Nếu UI đang phụ thuộc vào business logic hiện tại, phải kiểm tra cả logic phía sau.

---

# 17. DEPENDENCY

Không thêm package mới nếu package hiện tại đã giải quyết được yêu cầu.

Trước khi thêm dependency:

1. Kiểm tra package hiện tại.
2. Kiểm tra Python version.
3. Kiểm tra compatibility.
4. Kiểm tra project đang dùng package nào tương tự.
5. Đánh giá tác động đến deployment.

Không thay package chỉ vì package khác "tốt hơn" nếu không có yêu cầu thực tế.

---

# 18. TEST SAU MỌI THAY ĐỔI

> **Mọi thay đổi code đều phải được test lại.**

Tối thiểu:

```text
Edit
→ Run
→ Test affected feature
→ Check error/log
→ Verify expected result
```

Nếu project có test:

```text
Run targeted tests
→ Run related tests
→ Run broader test suite when appropriate
```

Nếu không có automated test:

> Phải thực hiện manual verification phù hợp với chức năng đã sửa.

Không được kết luận "đã sửa xong" chỉ vì code không báo syntax error.

---

# 19. TEST REGRESSION

Sau khi sửa một chức năng, phải kiểm tra những chức năng có liên quan.

Ví dụ:

```text
Sửa database query
→ test function
→ test API
→ test UI sử dụng API
```

Hoặc:

```text
Sửa import
→ test validation
→ test database write
→ test export/report liên quan
```

Mức độ regression test phải tương ứng với phạm vi ảnh hưởng.

---

# 20. KHÔNG TEST BẰNG CÁCH PHÁ DỮ LIỆU THẬT

Nếu có thể, sử dụng:

- test database
- test file
- sample data
- mock
- temporary directory
- isolated environment

Không tùy tiện chạy thao tác destructive trên dữ liệu production.

Nếu bắt buộc thao tác trên dữ liệu thật:

> Phải xác định rõ rủi ro và có backup/rollback phù hợp.

---

# 21. KIỂM TRA SAU KHI SỬA

Sau mỗi thay đổi quan trọng phải kiểm tra:

```text
Code chạy?
↓
Không có error mới?
↓
Kết quả đúng?
↓
Dữ liệu đúng?
↓
Behavior cũ còn hoạt động?
↓
Không ảnh hưởng chức năng liên quan?
```

Nếu có test failure:

> Không được bỏ qua test chỉ để task trở thành "pass".

Phải xác định:

```text
Test sai?
Hay code sai?
Hay assumption sai?
```

---

# 22. ROOT CAUSE > SYMPTOM

Khi sửa bug:

Không chỉ sửa triệu chứng.

Ví dụ:

```text
UI hiển thị sai
```

Không mặc định:

```text
→ sửa UI
```

Phải kiểm tra:

```text
Database
→ Query
→ Business logic
→ Data transformation
→ API
→ UI
```

Nếu nguyên nhân nằm ở data hoặc backend thì sửa đúng nơi gây ra lỗi.

---

# 23. GIỮ NGUYÊN PUBLIC INTERFACE

Nếu function/class/module đang được nơi khác sử dụng:

```python
function(...)
```

không tự ý đổi:

- tên
- parameters
- return type
- exception behavior

nếu không cần thiết.

Nếu bắt buộc thay đổi API/interface:

1. Tìm toàn bộ nơi sử dụng.
2. Cập nhật các caller.
3. Test tất cả caller.
4. Kiểm tra backward compatibility.

---

# 24. KHÔNG REWRITE TOÀN BỘ

Không rewrite một module hoặc project chỉ vì:

- code chưa đẹp
- code cũ
- có thể tối ưu
- có framework mới
- có cách viết ngắn hơn

Rewrite chỉ nên được thực hiện khi:

- yêu cầu rõ ràng
- implementation hiện tại không thể đáp ứng
- hoặc chi phí sửa nhỏ lẻ lớn hơn đáng kể so với thay đổi có kiểm soát

Ngay cả khi rewrite cần thiết, phải chia thành các bước nhỏ có thể kiểm tra.

---

# 25. PERFORMANCE

Không tối ưu performance theo cảm tính.

Trước khi tối ưu:

1. Xác định bottleneck.
2. Đo hoặc kiểm tra bằng evidence.
3. Xác định nguyên nhân.
4. Chọn thay đổi nhỏ nhất có hiệu quả.
5. Test lại behavior.

Không đổi architecture chỉ vì đoán rằng nó sẽ nhanh hơn.

---

# 26. FILES & PATH

Khi xử lý file:

- kiểm tra file tồn tại
- kiểm tra quyền truy cập
- kiểm tra encoding
- kiểm tra format
- xử lý path an toàn
- tránh hard-code path nếu project đã có config

Không tự ý đổi đường dẫn hoặc cấu trúc thư mục nếu không cần.

---

# 27. BACKWARD COMPATIBILITY

Khi thêm chức năng mới:

> Ưu tiên để dữ liệu, config và behavior cũ tiếp tục hoạt động.

Đặc biệt với:

- database
- JSON
- CSV
- Excel
- API
- config
- saved state
- cache

Nếu breaking change là bắt buộc, phải xác định rõ những thứ bị ảnh hưởng.

---

# 28. SCOPE CONTROL

Task chỉ nên thay đổi những gì cần thiết để hoàn thành yêu cầu.

Không tự tiện thêm:

- refactor
- feature mới
- UI redesign
- dependency mới
- database redesign
- rename
- cleanup lớn

nếu không liên quan trực tiếp.

Nếu phát hiện vấn đề ngoài scope:

> Ghi nhận và báo lại, không tự tiện sửa.

---

# 29. DOCUMENTATION

Nếu thay đổi làm thay đổi cách sử dụng hệ thống:

- cập nhật documentation liên quan
- cập nhật comment/docstring nếu cần
- không tạo documentation trùng lặp

Không viết documentation dài chỉ để mô tả những thứ đã rõ ràng trong code.

---

# 30. REVIEW TRƯỚC KHI KẾT THÚC

Trước khi kết luận task hoàn thành, phải tự kiểm tra:

### Code

- [ ] Có sửa đúng nơi cần sửa không?
- [ ] Có thay đổi ngoài scope không?
- [ ] Có duplicate logic không?
- [ ] Có thể reuse code hiện tại không?
- [ ] Có thay đổi cấu trúc source không cần thiết không?

### Data

- [ ] Dữ liệu cũ còn nguyên không?
- [ ] Có mất dữ liệu không?
- [ ] Có tạo duplicate không?
- [ ] Có thay đổi dữ liệu ngoài phạm vi không?

### Behavior

- [ ] Chức năng được yêu cầu hoạt động đúng không?
- [ ] Chức năng cũ còn hoạt động không?
- [ ] API/interface cũ còn tương thích không?
- [ ] Workflow hiện tại còn đúng không?

### Test

- [ ] Đã test chức năng vừa sửa chưa?
- [ ] Đã test các chức năng liên quan chưa?
- [ ] Có test failure nào bị bỏ qua không?
- [ ] Có lỗi runtime/log mới không?

### Deployment

- [ ] Dependency có thay đổi không?
- [ ] Config có thay đổi không?
- [ ] Path/file/resource có thay đổi không?
- [ ] Build/package có còn hoạt động không?

Nếu bất kỳ câu trả lời nào là:

```text
"Không biết"
```

thì:

> **Phải kiểm tra thêm trước khi kết luận hoàn thành.**

---

# 31. QUY TRÌNH CHUẨN CHO MỖI TASK

Mọi task nên được xử lý theo quy trình:

```text
1. Read the request
        ↓
2. Inspect project structure
        ↓
3. Find related code
        ↓
4. Understand current behavior
        ↓
5. Identify root cause / required change
        ↓
6. Check existing functions and reusable logic
        ↓
7. Define minimal change
        ↓
8. Implement
        ↓
9. Run syntax/static checks if applicable
        ↓
10. Run targeted tests
        ↓
11. Run regression tests when needed
        ↓
12. Verify data and behavior
        ↓
13. Review diff
        ↓
14. Report what changed and what was tested
```

---

# 32. NGUYÊN TẮC ƯU TIÊN

Khi phải lựa chọn giữa nhiều phương án, ưu tiên theo thứ tự:

```text
1. Correctness
2. Data integrity
3. Existing business rules
4. Existing behavior
5. Minimal code change
6. Reuse existing code
7. Backward compatibility
8. Testability
9. Maintainability
10. Performance optimization
11. Refactoring / code aesthetics
```

Không hy sinh tính đúng đắn hoặc dữ liệu để đổi lấy code "đẹp".

---

# 33. NGUYÊN TẮC "STOP AND ASK"

Phải dừng và hỏi lại hoặc nêu rõ assumption nếu:

- yêu cầu mâu thuẫn với behavior hiện tại
- business rule chưa rõ
- có nguy cơ mất dữ liệu
- không rõ record nào là đúng
- không rõ API contract
- không rõ expected result
- thay đổi có thể ảnh hưởng lớn đến hệ thống
- cần thay đổi architecture để thực hiện yêu cầu

Không tự suy đoán trong các trường hợp có rủi ro cao.

---

# 34. OUTPUT KHI HOÀN THÀNH TASK

Khi báo cáo task, nên nêu ngắn gọn:

```text
Changed:
- Những gì đã sửa.

Reason:
- Nguyên nhân / lý do sửa.

Files:
- Những file đã thay đổi.

Tests:
- Đã chạy test gì.
- Kết quả.

Impact:
- Những phần có thể bị ảnh hưởng.

Not changed:
- Những phần cố tình không thay đổi để giữ scope.
```

Không nói "đã hoàn thành" nếu chưa thực sự kiểm tra.

---

# 35. CORE RULES

Các nguyên tắc sau luôn có mức ưu tiên cao:

> **1. Không đoán khi có thể kiểm tra.**

> **2. Không sửa dữ liệu sai bằng workaround.**

> **3. Không sửa nhiều hơn mức cần thiết.**

> **4. Không thay đổi cấu trúc source nếu không cần.**

> **5. Luôn tìm code hiện có trước khi tạo code mới.**

> **6. Không duplicate business logic.**

> **7. Sau khi sửa code phải test lại.**

> **8. Không bỏ qua test failure.**

> **9. Không tự ý thay đổi behavior ngoài yêu cầu.**

> **10. Nếu chưa biết, phải kiểm tra thêm hoặc hỏi lại.**

> **11. Ưu tiên root cause thay vì symptom.**

> **12. Dữ liệu và tính đúng đắn quan trọng hơn việc code trông đẹp.**
