/**
 * Mock data cho chế độ Guest Demo
 * Dùng để test tất cả tính năng mà không cần đăng nhập hoặc gọi API
 */

export const GUEST_USER = {
  id: 'guest-user-001',
  email: 'guest@demo.com',
  full_name: 'Guest Demo',
};

export const GUEST_DOCUMENTS = [
  {
    id: 'guest-doc-1',
    user_id: 'guest-user-001',
    file_name: 'Lịch sử Việt Nam.pdf',
    file_url: null,
    file_type: 'pdf',
    summary_text:
      'Tài liệu tóm tắt lịch sử Việt Nam từ thời kỳ dựng nước đến hiện đại. ' +
      'Bao gồm các triều đại phong kiến, cuộc đấu tranh giành độc lập và thống nhất đất nước.',
    status: 'ready',
    created_at: new Date(Date.now() - 86400000 * 2).toISOString(),
  },
  {
    id: 'guest-doc-2',
    user_id: 'guest-user-001',
    file_name: 'Toán học Đại cương.docx',
    file_url: null,
    file_type: 'docx',
    summary_text:
      'Giáo trình toán học đại cương dành cho sinh viên năm nhất. ' +
      'Bao gồm: đại số tuyến tính, giải tích, xác suất thống kê và các phương trình vi phân cơ bản.',
    status: 'ready',
    created_at: new Date(Date.now() - 86400000).toISOString(),
  },
];

export const GUEST_QUIZ = {
  'guest-doc-1': {
    id: 'guest-quiz-1',
    document_id: 'guest-doc-1',
    title: 'Quiz: Lịch sử Việt Nam',
    difficulty: 'medium',
    num_questions: 10,
    is_shared: false,
    created_at: new Date().toISOString(),
    questions: [
      {
        id: 'q1', quiz_set_id: 'guest-quiz-1',
        question_text: 'Nước Văn Lang do ai thành lập?',
        options: { A: 'Hùng Vương', B: 'An Dương Vương', C: 'Lý Thái Tổ', D: 'Đinh Tiên Hoàng' },
        correct_answer: 'A',
        difficulty_label: 'easy',
        difficulty_score: 0.82,
      },
      {
        id: 'q2', quiz_set_id: 'guest-quiz-1',
        question_text: 'Chiến thắng Bạch Đằng năm 938 do ai lãnh đạo?',
        options: { A: 'Lý Thường Kiệt', B: 'Trần Hưng Đạo', C: 'Ngô Quyền', D: 'Đinh Bộ Lĩnh' },
        correct_answer: 'C',
        difficulty_label: 'easy',
        difficulty_score: 0.79,
      },
      {
        id: 'q3', quiz_set_id: 'guest-quiz-1',
        question_text: 'Kinh đô Thăng Long được xây dựng dưới triều đại nào?',
        options: { A: 'Đinh', B: 'Lý', C: 'Trần', D: 'Lê' },
        correct_answer: 'B',
        difficulty_label: 'medium',
        difficulty_score: 0.67,
      },
      {
        id: 'q4', quiz_set_id: 'guest-quiz-1',
        question_text: 'Năm 1945, nước Việt Nam Dân chủ Cộng hòa được thành lập vào ngày nào?',
        options: { A: '30/4/1975', B: '2/9/1945', C: '19/8/1945', D: '7/5/1954' },
        correct_answer: 'B',
        difficulty_label: 'medium',
        difficulty_score: 0.64,
      },
      {
        id: 'q5', quiz_set_id: 'guest-quiz-1',
        question_text: 'Trận Điện Biên Phủ kết thúc vào năm nào?',
        options: { A: '1945', B: '1950', C: '1954', D: '1975' },
        correct_answer: 'C',
        difficulty_label: 'medium',
        difficulty_score: 0.61,
      },
      {
        id: 'q6', quiz_set_id: 'guest-quiz-1',
        question_text: 'Nhà Trần chống quân Nguyên Mông tổng cộng bao nhiêu lần?',
        options: { A: '1 lần', B: '2 lần', C: '3 lần', D: '4 lần' },
        correct_answer: 'C',
        difficulty_label: 'hard',
        difficulty_score: 0.58,
      },
      {
        id: 'q7', quiz_set_id: 'guest-quiz-1',
        question_text: 'Tác giả của "Hịch tướng sĩ" là ai?',
        options: { A: 'Nguyễn Trãi', B: 'Trần Hưng Đạo', C: 'Lý Thường Kiệt', D: 'Ngô Quyền' },
        correct_answer: 'B',
        difficulty_label: 'hard',
        difficulty_score: 0.52,
      },
      {
        id: 'q8', quiz_set_id: 'guest-quiz-1',
        question_text: 'Đất nước Việt Nam thống nhất vào năm nào?',
        options: { A: '1954', B: '1968', C: '1973', D: '1975' },
        correct_answer: 'D',
        difficulty_label: 'medium',
        difficulty_score: 0.63,
      },
      {
        id: 'q9', quiz_set_id: 'guest-quiz-1',
        question_text: 'Triều đại nào ban hành Bộ luật Hồng Đức?',
        options: { A: 'Lý', B: 'Trần', C: 'Lê Sơ', D: 'Nguyễn' },
        correct_answer: 'C',
        difficulty_label: 'hard',
        difficulty_score: 0.55,
      },
      {
        id: 'q10', quiz_set_id: 'guest-quiz-1',
        question_text: 'Nguyễn Ái Quốc lấy tên Hồ Chí Minh từ năm nào?',
        options: { A: '1930', B: '1941', C: '1945', D: '1954' },
        correct_answer: 'B',
        difficulty_label: 'easy',
        difficulty_score: 0.74,
      },
    ],
  },
  'guest-doc-2': {
    id: 'guest-quiz-2',
    document_id: 'guest-doc-2',
    title: 'Quiz: Toán học Đại cương',
    difficulty: 'medium',
    num_questions: 10,
    is_shared: false,
    created_at: new Date().toISOString(),
    questions: [
      {
        id: 'mq1', quiz_set_id: 'guest-quiz-2',
        question_text: 'Đạo hàm của f(x) = x² là gì?',
        options: { A: 'x', B: '2x', C: 'x²', D: '2' },
        correct_answer: 'B',
        difficulty_label: 'easy',
        difficulty_score: 0.85,
      },
      {
        id: 'mq2', quiz_set_id: 'guest-quiz-2',
        question_text: 'Tích phân của f(x) = 1 là gì?',
        options: { A: '0', B: 'x', C: 'x + C', D: '1/x + C' },
        correct_answer: 'C',
        difficulty_label: 'easy',
        difficulty_score: 0.81,
      },
      {
        id: 'mq3', quiz_set_id: 'guest-quiz-2',
        question_text: 'Giới hạn lim(x→0) sin(x)/x bằng bao nhiêu?',
        options: { A: '0', B: '∞', C: '1', D: 'Không xác định' },
        correct_answer: 'C',
        difficulty_label: 'medium',
        difficulty_score: 0.65,
      },
      {
        id: 'mq4', quiz_set_id: 'guest-quiz-2',
        question_text: 'Ma trận đơn vị có tính chất gì?',
        options: { A: 'A·I = 0', B: 'A·I = A', C: 'A·I = I', D: 'I·I = 0' },
        correct_answer: 'B',
        difficulty_label: 'medium',
        difficulty_score: 0.62,
      },
      {
        id: 'mq5', quiz_set_id: 'guest-quiz-2',
        question_text: 'Xác suất của biến cố chắc chắn bằng bao nhiêu?',
        options: { A: '0', B: '0.5', C: '0.9', D: '1' },
        correct_answer: 'D',
        difficulty_label: 'easy',
        difficulty_score: 0.78,
      },
      {
        id: 'mq6', quiz_set_id: 'guest-quiz-2',
        question_text: 'Công thức Euler e^(iπ) + 1 = ?',
        options: { A: '2', B: '-1', C: '0', D: '1' },
        correct_answer: 'C',
        difficulty_label: 'hard',
        difficulty_score: 0.57,
      },
      {
        id: 'mq7', quiz_set_id: 'guest-quiz-2',
        question_text: 'Số phần tử của tập hợp lũy thừa của tập {a, b, c} là?',
        options: { A: '3', B: '6', C: '8', D: '9' },
        correct_answer: 'C',
        difficulty_label: 'medium',
        difficulty_score: 0.66,
      },
      {
        id: 'mq8', quiz_set_id: 'guest-quiz-2',
        question_text: 'Phương trình bậc hai ax² + bx + c = 0 có delta = b² - 4ac. Nếu delta < 0 thì?',
        options: { A: 'Có 2 nghiệm thực phân biệt', B: 'Có nghiệm kép', C: 'Vô nghiệm thực', D: 'Vô số nghiệm' },
        correct_answer: 'C',
        difficulty_label: 'hard',
        difficulty_score: 0.59,
      },
      {
        id: 'mq9', quiz_set_id: 'guest-quiz-2',
        question_text: 'log₂(8) bằng bao nhiêu?',
        options: { A: '2', B: '3', C: '4', D: '8' },
        correct_answer: 'B',
        difficulty_label: 'easy',
        difficulty_score: 0.83,
      },
      {
        id: 'mq10', quiz_set_id: 'guest-quiz-2',
        question_text: 'Tổng các góc của một tam giác bằng?',
        options: { A: '90°', B: '180°', C: '270°', D: '360°' },
        correct_answer: 'B',
        difficulty_label: 'easy',
        difficulty_score: 0.84,
      },
    ],
  },
};

export const GUEST_FLASHCARDS = {
  'guest-doc-1': [
    { id: 'f1', document_id: 'guest-doc-1', front_text: 'Nước Văn Lang', back_text: 'Nhà nước đầu tiên trong lịch sử Việt Nam, do Hùng Vương thành lập, tồn tại khoảng 2879-258 TCN.', created_at: new Date().toISOString() },
    { id: 'f2', document_id: 'guest-doc-1', front_text: 'Chiến thắng Bạch Đằng 938', back_text: 'Trận chiến do Ngô Quyền lãnh đạo, đánh bại quân Nam Hán, chấm dứt 1000 năm Bắc thuộc.', created_at: new Date().toISOString() },
    { id: 'f3', document_id: 'guest-doc-1', front_text: 'Hịch tướng sĩ', back_text: 'Áng văn bất hủ do Trần Hưng Đạo soạn, kêu gọi tướng sĩ quyết tâm đánh giặc Nguyên Mông.', created_at: new Date().toISOString() },
    { id: 'f4', document_id: 'guest-doc-1', front_text: 'Bộ luật Hồng Đức', back_text: 'Bộ luật ban hành dưới triều Lê Sơ (thế kỷ 15), là bộ luật hoàn chỉnh nhất trong lịch sử phong kiến Việt Nam.', created_at: new Date().toISOString() },
    { id: 'f5', document_id: 'guest-doc-1', front_text: '2/9/1945', back_text: 'Ngày Chủ tịch Hồ Chí Minh đọc Tuyên ngôn Độc lập, khai sinh nước Việt Nam Dân chủ Cộng hòa.', created_at: new Date().toISOString() },
    { id: 'f6', document_id: 'guest-doc-1', front_text: 'Chiến dịch Điện Biên Phủ', back_text: 'Chiến dịch quân sự năm 1954 do tướng Võ Nguyên Giáp chỉ huy, đánh bại thực dân Pháp, kết thúc kháng chiến.', created_at: new Date().toISOString() },
    { id: 'f7', document_id: 'guest-doc-1', front_text: 'Thống nhất đất nước', back_text: 'Ngày 30/4/1975, miền Nam hoàn toàn giải phóng. Đất nước thống nhất sau hơn 20 năm chia cắt.', created_at: new Date().toISOString() },
  ],
  'guest-doc-2': [
    { id: 'mf1', document_id: 'guest-doc-2', front_text: 'Đạo hàm', back_text: 'Tốc độ thay đổi của hàm số tại một điểm. f\'(x) = lim(h→0) [f(x+h) - f(x)] / h', created_at: new Date().toISOString() },
    { id: 'mf2', document_id: 'guest-doc-2', front_text: 'Tích phân xác định', back_text: 'Diện tích dưới đường cong từ a đến b: ∫ₐᵇ f(x)dx = F(b) - F(a), trong đó F là nguyên hàm của f.', created_at: new Date().toISOString() },
    { id: 'mf3', document_id: 'guest-doc-2', front_text: 'Ma trận', back_text: 'Bảng số hình chữ nhật m×n gồm m hàng và n cột. Dùng để biểu diễn hệ phương trình tuyến tính.', created_at: new Date().toISOString() },
    { id: 'mf4', document_id: 'guest-doc-2', front_text: 'Biến cố độc lập', back_text: 'Hai biến cố A và B độc lập khi P(A∩B) = P(A)·P(B). Xảy ra biến cố này không ảnh hưởng đến biến cố kia.', created_at: new Date().toISOString() },
    { id: 'mf5', document_id: 'guest-doc-2', front_text: 'Công thức Euler', back_text: 'e^(iθ) = cos(θ) + i·sin(θ). Đặc biệt: e^(iπ) + 1 = 0, được coi là đẳng thức đẹp nhất toán học.', created_at: new Date().toISOString() },
    { id: 'mf6', document_id: 'guest-doc-2', front_text: 'Giới hạn (Limit)', back_text: 'lim(x→a) f(x) = L có nghĩa là f(x) tiến đến L khi x tiến đến a. Nền tảng của giải tích.', created_at: new Date().toISOString() },
    { id: 'mf7', document_id: 'guest-doc-2', front_text: 'Chuỗi Taylor', back_text: 'Khai triển hàm số thành chuỗi lũy thừa: f(x) = Σ [f⁽ⁿ⁾(a)/n!] · (x-a)ⁿ', created_at: new Date().toISOString() },
  ],
};

// Map document_id → quiz_set_id để navigate đúng
export const GUEST_QUIZ_MAP = {
  'guest-doc-1': 'guest-quiz-1',
  'guest-doc-2': 'guest-quiz-2',
};
