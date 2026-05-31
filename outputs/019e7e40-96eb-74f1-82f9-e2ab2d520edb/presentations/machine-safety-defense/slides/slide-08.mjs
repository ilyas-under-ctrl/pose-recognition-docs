import { base, body, C, kicker, note, title } from "./common.mjs";

export async function slide08(presentation, ctx) {
  const slide = presentation.slides.add();
  base(slide, ctx, { footer: "RÃ©sultats: compromis d'alerte TCN et compromis de stop GRU" });
  kicker(slide, ctx, "RÃ©sultat principal", { color: C.green });
  title(slide, ctx, "Alerte opÃ©rateur et stop court horizon se lisent avec des mÃ©triques diffÃ©rentes.", { w: 980 });
  ctx.addShape(slide, { x: 64, y: 178, w: 548, h: 382, fill: C.white, line: ctx.line(C.blue, 2) });
  body(slide, ctx, "Alerte opÃ©rateur TCN", { x: 92, y: 204, w: 260, h: 34, size: 28, bold: true, color: C.blue });
  body(slide, ctx, "Sortie unique: risk_present_now", { x: 92, y: 244, w: 300, h: 24, size: 16, color: C.muted, face: ctx.fonts.mono });
  body(slide, ctx, "Seuil 0,55", { x: 92, y: 292, w: 160, h: 24, size: 18, bold: true, color: C.ink });
  body(slide, ctx, "Early 0,2", { x: 92, y: 328, w: 110, h: 20, size: 15, color: C.muted });
  body(slide, ctx, "0.850", { x: 96, y: 350, w: 92, h: 34, size: 28, bold: true, color: C.blue });
  body(slide, ctx, "Early 0,3", { x: 226, y: 328, w: 110, h: 20, size: 15, color: C.muted });
  body(slide, ctx, "0.642", { x: 230, y: 350, w: 92, h: 34, size: 28, bold: true, color: C.blue });
  body(slide, ctx, "PrÃ©cision", { x: 356, y: 328, w: 110, h: 20, size: 15, color: C.muted });
  body(slide, ctx, "0.859", { x: 360, y: 350, w: 92, h: 34, size: 28, bold: true, color: C.blue });
  body(slide, ctx, "FA/min", { x: 486, y: 328, w: 70, h: 20, size: 15, color: C.muted });
  body(slide, ctx, "1.574", { x: 486, y: 350, w: 92, h: 34, size: 28, bold: true, color: C.blue });
  body(slide, ctx, "Seuil 0,35 plus agressif: Early 0,3 = 0.683, mais prÃ©cision = 0.661 et FA/min = 6.015.", {
    x: 92,
    y: 420,
    w: 472,
    h: 66,
    size: 18,
  });
  note(slide, ctx, "Pour l'alerte opÃ©rateur, le seuil 0,55 garde une avance utile Ã  0,2-0,3 s tout en limitant le bruit continu.", {
    x: 92,
    y: 500,
    w: 472,
    h: 42,
    fill: C.blueSoft,
    line: C.blue,
    size: 15,
  });

  ctx.addShape(slide, { x: 660, y: 178, w: 556, h: 382, fill: C.white, line: ctx.line(C.red, 2) });
  body(slide, ctx, "Stop court horizon GRU", { x: 688, y: 204, w: 300, h: 34, size: 28, bold: true, color: C.red });
  body(slide, ctx, "Score: score_by_02", { x: 688, y: 244, w: 280, h: 24, size: 16, color: C.muted, face: ctx.fonts.mono });
  body(slide, ctx, "Seuil 0,95 strict", { x: 688, y: 292, w: 160, h: 24, size: 18, bold: true, color: C.ink });
  body(slide, ctx, "P(<=0,2 s)", { x: 688, y: 328, w: 110, h: 20, size: 15, color: C.muted });
  body(slide, ctx, "0.708", { x: 692, y: 350, w: 92, h: 34, size: 28, bold: true, color: C.red });
  body(slide, ctx, "P(<=0,3 s)", { x: 820, y: 328, w: 110, h: 20, size: 15, color: C.muted });
  body(slide, ctx, "0.903", { x: 824, y: 350, w: 92, h: 34, size: 28, bold: true, color: C.red });
  body(slide, ctx, "Temps moyen", { x: 952, y: 328, w: 110, h: 20, size: 15, color: C.muted });
  body(slide, ctx, "0.133 s", { x: 952, y: 350, w: 110, h: 34, size: 28, bold: true, color: C.red });
  body(slide, ctx, "Seuil 0,90 plus couvrant: P(<=0,2 s) = 0.502, P(<=0,3 s) = 0.741, temps moyen = 0.221 s.", {
    x: 688,
    y: 420,
    w: 488,
    h: 66,
    size: 18,
  });
  note(slide, ctx, "Pour le stop, le seuil 0,95 reste le point le plus crÃ©dible quand l'on veut agir seulement Ã  l'approche immÃ©diate de l'entrÃ©e.", {
    x: 688,
    y: 500,
    w: 488,
    h: 42,
    fill: C.redSoft,
    line: C.red,
    size: 15,
  });
  return slide;
}

