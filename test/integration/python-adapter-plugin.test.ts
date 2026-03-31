import { beforeEach, describe, expect, it, vi } from "vitest";
import { readFileSync } from "node:fs";

const searchViaPythonMock = vi.fn();
const contextPackViaPythonMock = vi.fn();
const storeViaPythonMock = vi.fn();
const statusViaPythonMock = vi.fn();
const onboardingViaPythonMock = vi.fn();
const rememberViaPythonMock = vi.fn();
const recallViaPythonMock = vi.fn();

vi.mock("../../src/python-adapter.js", () => ({
  searchViaPython: searchViaPythonMock,
  contextPackViaPython: contextPackViaPythonMock,
  storeViaPython: storeViaPythonMock,
  statusViaPython: statusViaPythonMock,
  onboardingViaPython: onboardingViaPythonMock,
  rememberViaPython: rememberViaPythonMock,
  recallViaPython: recallViaPythonMock,
  conflictPromptViaPython: vi.fn(),
  conflictResolveViaPython: vi.fn(),
  correctViaPython: vi.fn(),
  forgetViaPython: vi.fn(),
  getViaPython: vi.fn(),
  linkNeighborsViaPython: vi.fn(),
  linkStoreViaPython: vi.fn(),
  profileViaPython: vi.fn(),
  rebuildViaPython: vi.fn(),
  scanViaPython: vi.fn(),
  scopePolicyViaPython: vi.fn(),
  surfaceViaPython: vi.fn(),
  backupListViaPython: vi.fn(),
  backupPreviewViaPython: vi.fn(),
  backupDownloadViaPython: vi.fn(),
  backupUploadViaPython: vi.fn(),
  cleanViaPython: vi.fn(),
  doctorViaPython: vi.fn(),
  taxonomyCleanViaPython: vi.fn(),
  visualizeViaPython: vi.fn(),
}));

type RegisteredTool = {
  name: string;
  execute(toolCallId: string, params: Record<string, unknown>): Promise<any>;
};

function buildApi(pluginConfig?: Record<string, unknown>) {
  let tools: RegisteredTool[] = [];
  const events: Record<string, ((event: any, ctx: any) => Promise<any> | any)[]> = {};

  return {
    api: {
      pluginConfig,
      logger: {
        info: vi.fn(),
        warn: vi.fn(),
      },
      resolvePath: (input: string) => input,
      registerTool(factory: (ctx: Record<string, unknown>) => RegisteredTool[]) {
        tools = factory({
          agentId: "agent-1",
          workspaceDir: "/tmp/aegis-plugin-test",
          sessionKey: "session-1",
        });
      },
      on: vi.fn((name: string, handler: (event: any, ctx: any) => Promise<any> | any) => {
        events[name] ??= [];
        events[name].push(handler);
      }),
      registerService: vi.fn(),
    },
    getTools: () => tools,
    events,
  };
}

describe("TypeScript plugin Python retrieval adapter", () => {
  beforeEach(() => {
    vi.resetModules();
    searchViaPythonMock.mockReset();
    contextPackViaPythonMock.mockReset();
    storeViaPythonMock.mockReset();
    statusViaPythonMock.mockReset();
    onboardingViaPythonMock.mockReset();
    rememberViaPythonMock.mockReset();
    recallViaPythonMock.mockReset();
  });

  it("routes memory_search through Python", async () => {
    searchViaPythonMock.mockResolvedValue({
      mappedResults: [
        {
          path: "aegis://semantic/mem_1",
          startLine: 0,
          endLine: 0,
          score: 0.91,
          snippet: "SQLite FTS5 retrieval memory",
          source: "memory",
          citation: "[semantic] Strong semantic fact match.",
        },
      ],
      rawResults: [{ memory: { id: "mem_1", type: "semantic", content: "SQLite FTS5 retrieval memory" }, score: 0.91 }],
    });

    const { default: memoryPlugin } = await import("../../index.js");
    const harness = buildApi({ pythonToolAdapter: "force" });
    memoryPlugin.register(harness.api as any);
    const tool = harness.getTools().find((entry) => entry.name === "memory_search");

    const result = await tool!.execute("call-search", { query: "SQLite retrieval", limit: 5 });

    expect(searchViaPythonMock).toHaveBeenCalledOnce();
    expect(result.details.backend).toBe("python");
    expect(result.content[0].text).toContain("SQLite FTS5 retrieval memory");
  });

  it("routes memory_context_pack through Python", async () => {
    contextPackViaPythonMock.mockResolvedValue({
      backend: "python",
      strategy: { name: "mammoth_lexical_first" },
      results: [{ retrieval_stage: "lexical" }],
    });

    const { default: memoryPlugin } = await import("../../index.js");
    const harness = buildApi({ pythonToolAdapter: "force" });
    memoryPlugin.register(harness.api as any);
    const tool = harness.getTools().find((entry) => entry.name === "memory_context_pack");

    const result = await tool!.execute("call-context", { query: "mammoth route" });

    expect(contextPackViaPythonMock).toHaveBeenCalledOnce();
    expect(result.content[0].text).toContain("\"mammoth_lexical_first\"");
  });

  it("routes memory_store and memory_stats through Python", async () => {
    storeViaPythonMock.mockResolvedValue("Stored episodic memory mem_2.");
    statusViaPythonMock.mockResolvedValue({
      health_state: "HEALTHY",
      counts: { active: 2 },
      health: { state: "HEALTHY", issues: [], capabilities: { local_store: true } },
    });

    const { default: memoryPlugin } = await import("../../index.js");
    const harness = buildApi({ pythonToolAdapter: "force" });
    memoryPlugin.register(harness.api as any);
    const storeTool = harness.getTools().find((entry) => entry.name === "memory_store");
    const statsTool = harness.getTools().find((entry) => entry.name === "memory_stats");

    const stored = await storeTool!.execute("call-store", { text: "Remember this." });
    const stats = await statsTool!.execute("call-stats", {});

    expect(storeViaPythonMock).toHaveBeenCalledOnce();
    expect(statusViaPythonMock).toHaveBeenCalledOnce();
    expect(stored.content[0].text).toContain("Stored episodic memory");
    expect(stats.content[0].text).toContain("Aegis is ready and local memory is working normally.");
  });

  it("routes memory_setup through Python onboarding", async () => {
    onboardingViaPythonMock.mockResolvedValue({
      summary: "Aegis setup is ready.",
      backend: "python",
      ready: true,
    });

    const { default: memoryPlugin } = await import("../../index.js");
    const harness = buildApi({ pythonToolAdapter: "force" });
    memoryPlugin.register(harness.api as any);
    const setupTool = harness.getTools().find((entry) => entry.name === "memory_setup");

    const setup = await setupTool!.execute("call-setup", {});

    expect(onboardingViaPythonMock).toHaveBeenCalledOnce();
    expect(setup.content[0].text).toContain("Aegis setup is ready.");
    expect(setup.details.ready).toBe(true);
  });

  it("registers every manifest default tool in the runtime tool list", async () => {
    const manifest = JSON.parse(
      readFileSync("/home/hali/.openclaw/extensions/memory-aegis-v7/openclaw.plugin.json", "utf-8"),
    ) as {
      consumerSurface: { defaultTools: string[] };
    };

    const { default: memoryPlugin } = await import("../../index.js");
    const harness = buildApi({ pythonToolAdapter: "force" });
    memoryPlugin.register(harness.api as any);

    const runtimeToolNames = new Set(harness.getTools().map((entry) => entry.name));

    expect(manifest.consumerSurface.defaultTools.every((name) => runtimeToolNames.has(name))).toBe(true);
  });

  it("registers every manifest advanced tool in the runtime tool list", async () => {
    const manifest = JSON.parse(
      readFileSync("/home/hali/.openclaw/extensions/memory-aegis-v7/openclaw.plugin.json", "utf-8"),
    ) as {
      consumerSurface: { advancedTools: string[] };
    };

    const { default: memoryPlugin } = await import("../../index.js");
    const harness = buildApi({ pythonToolAdapter: "force" });
    memoryPlugin.register(harness.api as any);

    const runtimeToolNames = new Set(harness.getTools().map((entry) => entry.name));

    expect(manifest.consumerSurface.advancedTools.every((name) => runtimeToolNames.has(name))).toBe(true);
  });

  it("routes simple user verbs through Python", async () => {
    rememberViaPythonMock.mockResolvedValue("Remembered.");
    recallViaPythonMock.mockResolvedValue("Recalled.");

    const { default: memoryPlugin } = await import("../../index.js");
    const harness = buildApi({ pythonToolAdapter: "force" });
    memoryPlugin.register(harness.api as any);
    const rememberTool = harness.getTools().find((entry) => entry.name === "memory_remember");
    const recallTool = harness.getTools().find((entry) => entry.name === "memory_recall");

    const remembered = await rememberTool!.execute("call-remember", { content: "I like tea." });
    const recalled = await recallTool!.execute("call-recall", { query: "tea" });

    expect(rememberViaPythonMock).toHaveBeenCalledOnce();
    expect(recallViaPythonMock).toHaveBeenCalledOnce();
    expect(recallViaPythonMock).toHaveBeenCalledWith(
      expect.objectContaining({ query: "tea", scopeType: "agent", scopeId: "agent-1" }),
    );
    expect(remembered.content[0].text).toContain("Remembered.");
    expect(recalled.content[0].text).toContain("Recalled.");
  });

  it("uses Python-backed recall in before_agent_start", async () => {
    searchViaPythonMock.mockResolvedValue({
      mappedResults: [
        {
          path: "aegis://semantic/mem_1",
          startLine: 0,
          endLine: 0,
          score: 0.91,
          snippet: "SQLite FTS5 retrieval memory",
          source: "memory",
          citation: "[semantic] Strong semantic fact match.",
        },
      ],
      rawResults: [],
    });

    const { default: memoryPlugin } = await import("../../index.js");
    const harness = buildApi({ pythonToolAdapter: "force" });
    memoryPlugin.register(harness.api as any);

    const handler = harness.events.before_agent_start?.[0];
    const result = await handler?.({ prompt: "SQLite retrieval" }, { agentId: "agent-1", workspaceDir: "/tmp/aegis-plugin-test" });

    expect(searchViaPythonMock).toHaveBeenCalledOnce();
    expect(result.prependContext).toContain("Relevant Aegis memory context:");
    expect(result.prependContext).toContain("SQLite FTS5 retrieval memory");
  });
});
