"use strict";

const { createTruthKeepMemoryRuntime } = require("./truthkeep-memory.runtime.cjs");

module.exports = {
  id: "truthkeep-memory",
  kind: "memory",
  register(api) {
    api.registerMemoryRuntime(createTruthKeepMemoryRuntime());
  },
};
