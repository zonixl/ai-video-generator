/** 响应式尺寸工具 — 所有模板共享 */

/** 基于视频宽高计算响应式尺寸 */
export const responsive = (w: number, h: number) => {
  const aspect = w / h;
  const isPortrait = aspect < 1;
  return {
    /** 内容区宽度 — 竖屏 82%，横屏 68% */
    contentWidth: Math.round(isPortrait ? w * 0.82 : w * 0.68),
    /** 图片/卡片宽度 — 竖屏 84%，横屏 72% */
    cardWidth: Math.round(isPortrait ? w * 0.84 : w * 0.72),
    /** 标题宽度 — 竖屏 84%，横屏 70% */
    titleWidth: Math.round(isPortrait ? w * 0.84 : w * 0.7),
    /** 字幕宽度 */
    subtitleWidth: Math.round(isPortrait ? w * 0.82 : w * 0.68),
    /** 标题字号 — 基于宽度 */
    titleFontSize: Math.round(w * (isPortrait ? 0.062 : 0.04)),
    /** 副标题字号 */
    subtitleFontSize: Math.round(w * (isPortrait ? 0.033 : 0.02)),
    /** 装饰圆形尺寸 */
    orbSize: Math.round(w * (isPortrait ? 0.65 : 0.35)),
    /** 圆角 */
    borderRadius: Math.round(w * 0.03),
  };
};
