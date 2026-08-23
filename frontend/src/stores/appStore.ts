const KEY = "se-home-id";

function readId(): number {
  const raw = Number(localStorage.getItem(KEY) || 1);
  return raw === 2 ? 2 : 1;
}

export const appStore = {
  demoUser: "demo",
  demoDate: "2026-08-19",
  userId: readId(),
  setUserId(id: number) {
    this.userId = id === 2 ? 2 : 1;
    localStorage.setItem(KEY, String(this.userId));
    window.dispatchEvent(new Event("se-home-change"));
  },
};
