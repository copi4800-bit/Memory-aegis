import { AegisMemoryManager, closeAllManagers } from "../src/aegis-manager.js";
import { DEFAULT_AEGIS_CONFIG } from "../src/core/models.js";
import { nowISO, newId } from "../src/core/id.js";

async function runBenchmark() {
  console.log("==================================================");
  console.log("🪹 CHƯƠNG TRÌNH BENCHMARK WEAVER BIRD (PROCEDURAL RECALL)");
  console.log("==================================================\n");

  const manager = await AegisMemoryManager.create({
    agentId: "benchmark_weaver",
    workspaceDir: "/tmp/aegis_benchmark_weaver",
    config: DEFAULT_AEGIS_CONFIG
  });

  const db = manager.getDb();

  // 1. Dọn dẹp Mock Data
  db.prepare("DELETE FROM memory_nodes_vectors").run();
  db.prepare("DELETE FROM memory_nodes").run();

  // 2. Insert Dữ liệu Test
  const insertNode = db.prepare(`
    INSERT INTO memory_nodes (id, memory_type, content, canonical_subject, scope, status, importance, created_at, updated_at)
    VALUES (?, ?, ?, ?, 'session', 'active', 0.8, ?, ?)
  `);

  const now = nowISO();
  
  // Node A: Procedural (Cách build và deploy React)
  const nodeProcedureReact = newId();
  insertNode.run(
    nodeProcedureReact, 
    "procedural", 
    "# Mẫu Định Tuyến Quy Trình\nMục tiêu: Hướng dẫn build và deploy ứng dụng React\nTrình tự:\n1. run_command `npm run build`\n2. run_command `aws s3 sync build/ s3://my-bucket/`", 
    "workflow.procedure", now, now
  );

  // Node B: Factual (Kiến thức nền về React)
  const nodeFactReact = newId();
  insertNode.run(
    nodeFactReact, 
    "semantic_fact", 
    "React là một thư viện JavaScript declarative, efficient, và flexible để xây dựng ứng dụng giao diện (UI). Nó chia UI thành các component độc lập.", 
    "technical.stack", now, now
  );

  // Node C: Procedural (Cách optimize database PostgreSQL)
  const nodeProcedureDB = newId();
  insertNode.run(
    nodeProcedureDB, 
    "procedural", 
    "# Mẫu Định Tuyến Quy Trình\nMục tiêu: Tối ưu index cho PostgreSQL\nTrình tự:\n1. view_file `schema.sql`\n2. run_command `psql -c 'CREATE INDEX concurrent ...'`", 
    "workflow.procedure", now, now
  );

  console.log("[Data] Đã giả lập 3 Node:");
  console.log("  - Node P1 (Procedural): 'Hướng dẫn build và deploy ứng dụng React...'");
  console.log("  - Node F1 (Factual)   : 'React là một thư viện JavaScript declarative...'");
  console.log("  - Node P2 (Procedural): 'Tối ưu index cho PostgreSQL...'");
  console.log("--------------------------------------------------\n");

  // TEST 1: Truy vấn How-to (Procedural Intent)
  const q1 = "Làm cách nào để build và deploy ứng dụng React?";
  console.log(`[Test 1] Query: "${q1}"`);
  
  const res1 = await manager.search(q1, { maxResults: 5 });
  console.log(`Kết quả Test 1 (${res1.length} nodes):`);
  let hitProceduralFirst = false;
  res1.forEach((r: any, i) => {
    const nodeId = r.path.split("/").pop();
    const node = db.prepare("SELECT memory_type, content, id FROM memory_nodes WHERE id = ?").get(nodeId) as any;
    console.log(`  ${i + 1}. [${node.memory_type}] Score: ${r.score.toFixed(3)} | ${node.content.substring(0, 60).replace(/\n/g, " ")}`);
    if (i === 0 && node.memory_type === "procedural" && node.id === nodeProcedureReact) hitProceduralFirst = true;
  });

  // TEST 2: Truy vấn What-is (Factual Intent)
  const q2 = "Thư viện React là gì, dùng để làm gì?";
  console.log(`\n[Test 2] Query: "${q2}"`);
  
  const res2 = await manager.search(q2, { maxResults: 5 });
  console.log(`Kết quả Test 2 (${res2.length} nodes):`);
  let hitFactFirst = false;
  res2.forEach((r: any, i) => {
    const nodeId = r.path.split("/").pop();
    const node = db.prepare("SELECT memory_type, content, id FROM memory_nodes WHERE id = ?").get(nodeId) as any;
    console.log(`  ${i + 1}. [${node.memory_type}] Score: ${r.score.toFixed(3)} | ${node.content.substring(0, 60).replace(/\n/g, " ")}`);
    if (i === 0 && node.memory_type === "semantic_fact" && node.id === nodeFactReact) hitFactFirst = true;
  });

  console.log("\n================ TRẢ LỜI CÂU HỎI BENCHMARK WEAVER ================");
  console.log(`1. Task tương tự có recall procedural chuẩn không? => ${hitProceduralFirst ? "CÓ" : "KHÔNG"}`);
  console.log(`2. Procedural bonus (+0.5) có đè nát Fact khi hỏi khái niệm không? => ${hitFactFirst ? "ĐÃ CÂN BẰNG. Fact lấn lướt nhờ FTS/Lexical cao hơn." : "BỊ OVERRIDE. Cần giảm bonus procedural."}`);
  console.log("=================================================================\n");

  await closeAllManagers();
}

runBenchmark().catch(console.error);
