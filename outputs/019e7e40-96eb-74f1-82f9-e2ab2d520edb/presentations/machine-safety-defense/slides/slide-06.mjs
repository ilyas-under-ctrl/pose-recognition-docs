import { base, body, C, kicker, title } from "./common.mjs";

export async function slide06(presentation, ctx) {
  const slide = presentation.slides.add();
  base(slide, ctx, { footer: "Soutenance sÃ©curitÃ© machine" });
  kicker(slide, ctx, "Architecture", { color: C.green });
  title(slide, ctx, "Le pipeline final confie l'alerte au TCN et l'imminence d'arrÃªt au GRU.", { w: 980 });
  const cards = [
    [86, 202, C.green, "TCN warning / risk_present_now", "EntrÃ©e 60 x 54\nConv1d 54 -> 96\n4 blocs TCN rÃ©siduels\nDilatations 1,2,4,8\nMoyenne + dernier pas\nMLP 192 -> 96 -> 1\nSortie unique: risk_present_now"],
    [662, 202, C.red, "GRU exact-entry / score_by_02", "EntrÃ©e 30 x 54\nGRU 2 couches, hidden 96\nDropout 0,20\nMLP sur derniÃ¨re sortie\nScore: score_by_02\nLecture stop Ã  0,2 s et 0,3 s"],
  ];
  for (const [x, y, color, head, details] of cards) {
    ctx.addShape(slide, { x, y, w: 500, h: 310, fill: C.white, line: ctx.line(color, 3) });
    body(slide, ctx, head, { x: x + 28, y: y + 24, w: 420, h: 34, size: 26, bold: true, color });
    body(slide, ctx, details, { x: x + 28, y: y + 78, w: 420, h: 210, size: 19, face: ctx.fonts.mono });
  }
  body(slide, ctx, "Les deux modÃ¨les lisent les mÃªmes features causales et interviennent Ã  deux niveaux de la dÃ©cision de sÃ©curitÃ©.", {
    x: 92,
    y: 566,
    w: 940,
    h: 54,
    size: 20,
  });
  return slide;
}

