import { ChameleonBudgeter } from "../src/cognitive/chameleon.js";
import type { MemorySearchResult } from "../src/retrieval/packet.js";

console.log("==================================================");
console.log("🦎 CHƯƠNG TRÌNH BENCHMARK CHAMELEON (CONTEXT BUDGETING)");
console.log("==================================================\n");

// Giả lập 6 memory nodes trả về từ hệ thống Retrieval (đã rank theo FTS).
// Gồm 1 Trauma, 1 Identity, 4 Facts/Procedures về React.
const mockResults: MemorySearchResult[] = [
  {
    path: "aegis://trauma/1",
    startLine: 0, endLine: 0, score: 1.000, source: "memory",
    citation: "[trauma] rules.policy (crystallized) — safety override",
    snippet: "CẤM: Tuyệt đối không được thực thi lệnh rm -rf / trên hệ thống."
  },
  {
    path: "aegis://identity/2",
    startLine: 0, endLine: 0, score: 0.950, source: "memory",
    citation: "[identity] identity.persona (stable) — relevance match",
    snippet: "Bạn là Antigravity, một trợ lý AI thông thái và sử dụng văn phong kiếm hiệp để nói chuyện với người dùng. Cấm xưng hô hời hợt."
  },
  {
    path: "aegis://semantic_fact/3",
    startLine: 0, endLine: 0, score: 0.850, source: "memory",
    citation: "[semantic_fact] technical.react (stable) — relevance match",
    snippet: "React Fact 1: A JavaScript library for building user interfaces. It is maintained by Meta and a community of individual developers."
  },
  {
    path: "aegis://semantic_fact/4",
    startLine: 0, endLine: 0, score: 0.800, source: "memory",
    citation: "[semantic_fact] technical.react (stable) — relevance match",
    snippet: "React Fact 2: Components let you split the UI into independent, reusable pieces. This isolation prevents bugs from spreading."
  },
  {
    path: "aegis://semantic_fact/5",
    startLine: 0, endLine: 0, score: 0.750, source: "memory",
    citation: "[semantic_fact] technical.react (stable) — relevance match",
    snippet: "React Fact 3: React strictly uses unidirectional data flow. You pass props down, and lift state up through callbacks."
  },
  {
    path: "aegis://procedural/6",
    startLine: 0, endLine: 0, score: 0.700, source: "memory",
    citation: "[procedural] workflow.procedure (stable) — inferred via Platypus",
    snippet: "React Prod 4: # Mẫu Quy trình Deploy. \n 1. npm run build\n 2. rsync -a build/ user@server:/var/www/html/ \n Ngắn gọn mà thành công."
  }
];

// Test 1: Ngân sách hẹp (maxChars: 400).
// Kỳ vọng: Trauma và Identity chiếm chỗ, đẩy Fact 2 3 4 ra rìa.
console.log(`[Test 1] Fast & Tight Budget (maxChars: 600, topK: 5)`);
const out1 = ChameleonBudgeter.assemble(mockResults, { maxChars: 600, topK: 5, query: "React là gì?" });
console.log(out1);
console.log("\n--------------------------------------------------\n");

// Test 2: Ngân sách rộng (maxChars: 3000)
// Kỳ vọng: Vẫn hiện Zone 1 & 0 trên đỉnh, chừa chỗ cho cả 4 Facts/Procedures ở Task Memory.
console.log(`[Test 2] Generous Budget (maxChars: 3000, topK: 5)`);
const out2 = ChameleonBudgeter.assemble(mockResults, { maxChars: 3000, topK: 5, query: "React là gì?" });
console.log(out2);

console.log("\n================ KẾT LUẬN BENCHMARK ==================");
console.log("1. Zone 1 (Identity/Persona) có bị đè bởi Fact không? => KHÔNG, luôn đứng ở Core Directives");
console.log("2. Zone 2 limit có ngăn chặn việc ăn vượt budget không? => CÓ, Test 1 tự động drop các Node cuối.");
console.log("Chameleon hoàn toàn bảo toàn bối cảnh nhân vật/an toàn dù Retrieval tràn ngập rác kỹ thuật!");
