/**
 * 测试环境准备。
 * jsdom 在某些版本/选项下提供的 localStorage 只有壳、没有 setItem，
 * 这里检查方法可用性，不可用就补一个最小实现。
 */
const ls = globalThis.localStorage as Storage | undefined;

if (!ls || typeof ls.setItem !== "function") {
  const store = new Map<string, string>();
  globalThis.localStorage = {
    getItem: (k: string) => (store.has(k) ? store.get(k)! : null),
    setItem: (k: string, v: string) => void store.set(k, String(v)),
    removeItem: (k: string) => void store.delete(k),
    clear: () => store.clear(),
    key: (i: number) => Array.from(store.keys())[i] ?? null,
    get length() {
      return store.size;
    },
  } as Storage;
}
