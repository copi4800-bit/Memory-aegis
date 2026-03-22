import { AegisMemoryManager, closeAllManagers } from "../src/aegis-manager.js";
import { DEFAULT_AEGIS_CONFIG } from "../src/core/models.js";

async function runDoctor() {
  console.log("==================================================");
  console.log("🏥 ĐANG KHÁM SỨC KHỎE CHO AEGIS (MEMORY DOCTOR)");
  console.log("==================================================\n");

  const workspaceDir = "/home/hali/.openclaw/workspace";
  
  try {
    const manager = await AegisMemoryManager.create({
      agentId: "doctor_check",
      workspaceDir: workspaceDir,
      config: DEFAULT_AEGIS_CONFIG
    });

    const { text, data } = await manager.diagnose();
    
    console.log(text);
    
    if (data.summary.status === "healthy") {
      console.log("\n🚀 CHÚC MỪNG ĐẠI CA! Hệ thống đang ở trạng thái Sung Sức nhất.");
    } else if (data.summary.status === "degraded") {
      console.log("\n⚠️ CẢNH BÁO: Có một vài triệu chứng cần lưu ý nhưng não bộ vẫn hoạt động được.");
    } else {
      console.log("\n🔥 NGUY HIỂM: Hệ thống đang bị 'đột quỵ', cần can thiệp kỹ thuật ngay!");
    }

  } catch (err) {
    console.error("\n❌ LỖI KHI ĐANG KHÁM BỆNH:", err);
  } finally {
    await closeAllManagers();
  }
}

runDoctor();
