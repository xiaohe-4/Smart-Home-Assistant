export function useAsync<T>(loader: () => Promise<T>, deps: unknown[] = []) {
  return { loader, deps };
}
