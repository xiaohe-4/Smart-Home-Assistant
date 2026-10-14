type Rec = {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  onresult: ((event: { results: ArrayLike<{ 0: { transcript: string }; isFinal: boolean }> }) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
};

const DIGITS = "零一二三四五六七八九";

function RecognitionCtor(): (new () => Rec) | null {
  const w = window as unknown as { SpeechRecognition?: new () => Rec; webkitSpeechRecognition?: new () => Rec };
  return w.SpeechRecognition || w.webkitSpeechRecognition || null;
}

export function canListen() {
  return Boolean(RecognitionCtor());
}

function intToZh(n: number): string {
  if (!Number.isFinite(n)) return String(n);
  n = Math.round(Math.abs(n));
  if (n < 10) return DIGITS[n];
  if (n < 100) {
    const tens = Math.floor(n / 10);
    const ones = n % 10;
    const head = tens === 1 ? "十" : `${DIGITS[tens]}十`;
    return ones ? head + DIGITS[ones] : head;
  }
  if (n < 1000) {
    const hundreds = Math.floor(n / 100);
    const rest = n % 100;
    const head = `${DIGITS[hundreds]}百`;
    if (!rest) return head;
    if (rest < 10) return `${head}零${DIGITS[rest]}`;
    if (rest < 20) return `${head}一${intToZh(rest)}`;
    return head + intToZh(rest);
  }
  if (n < 10000) {
    const thousand = Math.floor(n / 1000);
    const rest = n % 1000;
    const head = `${DIGITS[thousand]}千`;
    if (!rest) return head;
    if (rest < 100) return `${head}零${intToZh(rest)}`;
    return head + intToZh(rest);
  }
  return String(n);
}

function scoreVoice(voice: SpeechSynthesisVoice) {
  const name = `${voice.name} ${voice.lang}`.toLowerCase();
  let score = 0;
  if (/zh[-_]cn|cmn-hans|chinese.*china/.test(name)) score += 8;
  if (/neural|natural|online|自然|云/.test(name)) score += 60;
  if (/yunxi|yunyang|yunjian|yunfeng|云希|云扬/.test(name)) score += 50;
  if (/xiaoxiao|xiaoyi|xiaohan|xiaomo|xiaoxuan|晓晓|晓伊/.test(name)) score += 42;
  if (/huihui|yaoyao|kangkang/.test(name)) score += 6;
  if (voice.localService === false) score += 12;
  return score;
}

function pickVoice(): SpeechSynthesisVoice | undefined {
  const voices = window.speechSynthesis.getVoices();
  const zh = voices.filter((v) => v.lang.toLowerCase().startsWith("zh") || /chinese|中文/i.test(v.name));
  if (!zh.length) return voices.find((v) => v.default);
  return [...zh].sort((a, b) => scoreVoice(b) - scoreVoice(a))[0];
}

export function forSpeech(text: string) {
  let spoken = text
    .replace(/kWh/gi, "千瓦时")
    .replace(/kW/gi, "千瓦")
    .replace(/(\d+(?:\.\d+)?)\s*[Ww]\b/g, "$1瓦")
    .replace(/℃|°C/g, "度")
    .replace(/XGBoostRegressor|XGBoost/gi, "预测模型")
    .replace(/MAPE/g, "平均误差")
    .replace(/R²|R2/g, "拟合优度")
    .replace(/(\d{1,2}):(\d{2})(?:\:\d{2})?/g, (_, h, m) => `${intToZh(Number(h))}点${intToZh(Number(m))}分`);

  spoken = spoken.replace(/(\d+)\.(\d+)/g, (_, whole, frac) => {
    const tail = [...String(frac)].map((d) => DIGITS[Number(d)] || d).join("");
    return `${intToZh(Number(whole))}点${tail}`;
  });
  spoken = spoken.replace(/\d{1,4}/g, (raw) => {
    const n = Number(raw);
    if (n >= 1900 && n <= 2100) return raw;
    return intToZh(n);
  });

  spoken = spoken
    .replace(/[;；]/g, "，")
    .replace(/。+/g, "，")
    .replace(/，+/g, "，")
    .replace(/^，|，$/g, "");
  if (!/[。！？]$/.test(spoken)) spoken += "。";
  return spoken;
}

export function speak(text: string, onEnd?: () => void) {
  if (!window.speechSynthesis) {
    onEnd?.();
    return;
  }
  const run = () => {
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(forSpeech(text));
    const voice = pickVoice();
    if (voice) {
      utter.voice = voice;
      utter.lang = voice.lang || "zh-CN";
    } else {
      utter.lang = "zh-CN";
    }
    const neural = voice ? /neural|natural|online|xiaoxiao|yunxi|yunyang|晓晓|云希/i.test(`${voice.name} ${voice.lang}`) : false;
    utter.rate = neural ? 1.08 : 1.12;
    utter.pitch = neural ? 1.06 : 1.18;
    utter.volume = 1;
    let finished = false;
    const done = () => {
      if (finished) return;
      finished = true;
      window.clearTimeout(guard);
      onEnd?.();
    };
    const guard = window.setTimeout(done, Math.min(16000, 1800 + text.length * 140));
    utter.onend = done;
    utter.onerror = done;
    window.setTimeout(() => {
      window.speechSynthesis.resume();
      window.speechSynthesis.speak(utter);
    }, 40);
  };

  if (window.speechSynthesis.getVoices().length) {
    run();
    return;
  }
  let started = false;
  const once = () => {
    if (started) return;
    started = true;
    window.speechSynthesis.removeEventListener("voiceschanged", once);
    run();
  };
  window.speechSynthesis.addEventListener("voiceschanged", once);
  window.setTimeout(once, 280);
}

if (typeof window !== "undefined" && window.speechSynthesis) {
  window.speechSynthesis.getVoices();
}

export function listenOnce(onText: (text: string, final: boolean) => void): () => void {
  const Ctor = RecognitionCtor();
  if (!Ctor) {
    onText("", true);
    return () => undefined;
  }
  const rec = new Ctor();
  rec.lang = "zh-CN";
  rec.interimResults = true;
  rec.continuous = false;
  rec.onresult = (event) => {
    const result = event.results[event.results.length - 1];
    onText(result[0].transcript, result.isFinal);
  };
  rec.onerror = () => onText("", true);
  rec.onend = () => onText("", true);
  try {
    rec.start();
  } catch {
    onText("", true);
  }
  return () => {
    try { rec.stop(); } catch { /* 已经停了 */ }
  };
}
