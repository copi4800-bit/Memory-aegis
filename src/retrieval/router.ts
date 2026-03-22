import type { MemorySearchResult } from "./packet.js";
import { ChameleonBudgeter, type RouterBudget, type ZonePolicy, ZONE_POLICIES } from "../cognitive/chameleon.js";

export type { RouterBudget, ZonePolicy };
export { ZONE_POLICIES };

export class AegisRouter {
  /**
   * Hàm "Cảnh sát giao thông" - Điều tiết luồng ký ức nạp vào AI.
   * Hiện tại đã được tiếp quản bởi Chameleon (Context Budgeting).
   */
  static enforce(results: MemorySearchResult[], budget: RouterBudget): string {
    return ChameleonBudgeter.assemble(results, budget);
  }
}
