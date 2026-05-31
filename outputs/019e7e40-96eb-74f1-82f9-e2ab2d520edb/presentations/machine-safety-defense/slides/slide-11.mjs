import { base, body, bullet, C, kicker, title } from "./common.mjs";

export async function slide11(presentation, ctx) {
  const slide = presentation.slides.add();
  base(slide, ctx, { dark: true, footer: "Conclure par les gains, puis les perspectives" });
  kicker(slide, ctx, "Conclusion", { color: "#86EFAC" });
  title(slide, ctx, "Le gain: une chaîne causale complète, pas seulement un classifieur.", { color: "#F9FAFB", w: 900 });
  ctx.addShape(slide, { x: 78, y: 188, w: 510, h: 340, fill: "#172033", line: ctx.line("#334155", 1) });
  body(slide, ctx, "Ce qui marche", { x: 106, y: 216, w: 420, h: 34, size: 27, bold: true, color: "#F9FAFB" });
  bullet(slide, ctx, [
    "Annotation dédiée: entrée physique et début du risque",
    "Variables pose-zone avec fenêtres causales",
    "Signal TCN d'alerte continue et GRU de stop imminent",
    "Politique d'alerte avec attention et blouse",
  ], { x: 108, y: 276, w: 420, size: 17, color: "#86EFAC", textColor: "#E5E7EB", gap: 54 });
  ctx.addShape(slide, { x: 668, y: 188, w: 510, h: 340, fill: "#172033", line: ctx.line("#334155", 1) });
  body(slide, ctx, "Prochaines étapes", { x: 696, y: 216, w: 420, h: 34, size: 27, bold: true, color: "#F9FAFB" });
  bullet(slide, ctx, [
    "Plus d'acteurs, vrais négatifs, machines et angles",
    "Multi-angle ou profondeur pour valider le volume 3D",
    "Latence complète: caméra jusqu'à mécanique",
    "Évaluation de sûreté au-delà de la classification",
  ], { x: 698, y: 276, w: 420, size: 17, color: "#FCA5A5", textColor: "#E5E7EB", gap: 54 });
  body(slide, ctx, "Phrase finale: c'est un prototype contrôlé avec un signal de sécurité utile; la suite est de prouver la robustesse hors scénario.", {
    x: 98,
    y: 586,
    w: 1000,
    h: 54,
    size: 20,
    color: "#CBD5E1",
  });
  return slide;
}
