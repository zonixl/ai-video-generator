import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {Check, Code2, FileText, Monitor, Palette, Settings2, Sparkles, Wrench} from 'lucide-react';
import type {ComponentSpec, RemotionSceneSpec, SceneLayout} from '../schema';
import {Icon} from '../components/Icon';

const ink = '#223142';
const muted = '#697482';
const paper = '#f7efdc';
const orange = '#f2a93b';
const green = '#17472e';
const blue = '#58aeda';
const red = '#d54532';

const clamp = (value: number, min: number, max: number) => Math.max(min, Math.min(max, value));

const compactText = (text = '', limit = 28) => {
  const clean = text.replace(/\s+/g, ' ').trim();
  return clean.length > limit ? `${clean.slice(0, limit - 1)}...` : clean;
};

const wrapText = (text = '', lineLimit: number, maxLines = 3) => {
  const clean = text.replace(/\s+/g, ' ').trim();
  if (!clean) return [];
  const lines: string[] = [];
  for (let index = 0; index < clean.length && lines.length < maxLines; index += lineLimit) {
    lines.push(clean.slice(index, index + lineLimit));
  }
  if (clean.length > lineLimit * maxLines && lines.length) {
    lines[lines.length - 1] = clean.slice(lineLimit * (maxLines - 1));
  }
  return lines;
};

const splitParts = (text = '') =>
  text
    .split(/[;|、，,]/)
    .map((part) => part.trim())
    .filter(Boolean);

const seedFromId = (id: string) => {
  let hash = 0;
  for (let i = 0; i < id.length; i++) {
    hash = (hash << 5) - hash + id.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash % 1000) / 1000;
};

const entrance = (frame: number, fps: number, order: number, kind: 'soft' | 'pop' | 'draw' = 'soft') => {
  const delay = (0.18 + order * 0.22) * fps;
  const p = spring({
    frame: frame - delay,
    fps,
    config: kind === 'pop' ? {damping: 11, stiffness: 180, mass: 0.75} : {damping: 18, stiffness: 95, mass: 0.9},
  });
  const opacity = interpolate(frame, [delay, delay + 8], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return {p, opacity, delay};
};

const PaperBackground: React.FC = () => {
  const frame = useCurrentFrame();
  const drift = Math.sin(frame / 96) * 0.035;
  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        background: paper,
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage:
            'linear-gradient(rgba(88,78,52,0.075) 1px, transparent 1px), linear-gradient(90deg, rgba(88,78,52,0.075) 1px, transparent 1px)',
          backgroundSize: '26px 26px',
          opacity: 0.82,
        }}
      />
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage:
            `radial-gradient(circle at 24% 14%, rgba(242,169,59,${0.13 + drift}), transparent 28%), radial-gradient(circle at 82% 22%, rgba(88,174,218,${0.11 - drift}), transparent 30%), radial-gradient(circle at 52% 84%, rgba(23,71,46,0.08), transparent 36%)`,
        }}
      />
      <div
        style={{
          position: 'absolute',
          inset: 0,
          boxShadow: 'inset 0 0 120px rgba(95,75,43,0.12)',
        }}
      />
    </div>
  );
};

const TopHeader: React.FC<{scene: RemotionSceneSpec; isPortrait: boolean}> = ({scene, isPortrait}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const {p, opacity} = entrance(frame, fps, 0, 'soft');
  const top = isPortrait ? height * 0.075 : height * 0.08;
  const fontSize = clamp(width * (isPortrait ? 0.046 : 0.031), 30, 54);
  return (
    <div
      style={{
        position: 'absolute',
        left: width * (isPortrait ? 0.09 : 0.2),
        right: width * (isPortrait ? 0.09 : 0.2),
        top,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        gap: width * 0.018,
        opacity,
        transform: `translateY(${(1 - p) * -16}px)`,
        color: ink,
        zIndex: 5,
      }}
    >
      <span
        style={{
          height: 2,
          flex: 1,
          maxWidth: width * 0.16,
          background: 'rgba(34,49,66,0.12)',
        }}
      />
      <span style={{fontSize, fontWeight: 800, fontFamily: '"Microsoft YaHei", "PingFang SC", serif'}}>
        {compactText(scene.headline || '核心知识点', isPortrait ? 14 : 22)}
      </span>
      <Sparkles size={fontSize * 0.78} color={orange} strokeWidth={2.5} />
      <span
        style={{
          height: 2,
          flex: 1,
          maxWidth: width * 0.16,
          background: 'rgba(34,49,66,0.12)',
        }}
      />
    </div>
  );
};

const SketchCard: React.FC<{
  component: ComponentSpec;
  style: React.CSSProperties;
  order: number;
  tone?: 'paper' | 'orange' | 'green';
}> = ({component, style, order, tone = 'paper'}) => {
  const frame = useCurrentFrame();
  const {fps, width} = useVideoConfig();
  const seed = seedFromId(component.id);
  const {p, opacity} = entrance(frame, fps, order, tone === 'green' ? 'pop' : 'soft');
  const rotate = (seed - 0.5) * 2.2;
  const isGreen = tone === 'green' || component.variant === 'success';
  const isOrange = tone === 'orange' || component.variant === 'warning';
  const bg = isGreen ? green : isOrange ? orange : 'rgba(255,250,239,0.9)';
  const color = isGreen ? '#fffaf0' : ink;
  const border = isGreen ? 'rgba(91,64,20,0.65)' : 'rgba(34,49,66,0.82)';
  const fontSize = clamp(width * 0.03, 24, 44);
  const iconColor = isGreen ? '#f7c65b' : component.variant === 'danger' ? red : isOrange ? ink : blue;

  return (
    <div
      style={{
        position: 'absolute',
        ...style,
        opacity,
        transform: `translateY(${(1 - p) * 22}px) scale(${0.96 + p * 0.04}) rotate(${rotate}deg)`,
        zIndex: 10 + order,
      }}
    >
      <div
        style={{
          width: '100%',
          height: '100%',
          minHeight: 92,
          border: `2.5px solid ${border}`,
          borderRadius: isGreen ? 7 : 8,
          background: bg,
          boxShadow: isGreen ? '8px 9px 0 rgba(112,82,27,0.32)' : '5px 7px 0 rgba(34,49,66,0.12)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexDirection: 'column',
          gap: 12,
          padding: '16px 20px',
          color,
          textAlign: 'center',
          boxSizing: 'border-box',
          overflow: 'hidden',
        }}
      >
        {component.icon ? <Icon name={component.icon} size={fontSize * 0.96} color={iconColor} strokeWidth={2.5} /> : null}
        <div style={{fontSize, fontWeight: 850, lineHeight: 1.15}}>
          {compactText(component.text || '关键点', 22)}
        </div>
        {isGreen ? (
          <div style={{fontSize: fontSize * 0.5, opacity: 0.9, fontWeight: 650}}>一键完成</div>
        ) : null}
      </div>
      {component.motion === 'strike' || component.variant === 'danger' ? (
        <StrikeLine order={order + 0.4} />
      ) : null}
    </div>
  );
};

const StrikeLine: React.FC<{order: number}> = ({order}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {p} = entrance(frame, fps, order, 'draw');
  return (
    <div
      style={{
        position: 'absolute',
        left: '14%',
        right: `${86 - p * 72}%`,
        top: '50%',
        height: 5,
        background: red,
        borderRadius: 99,
        transform: 'rotate(-2deg)',
        boxShadow: '0 1px 0 rgba(255,255,255,0.55)',
      }}
    />
  );
};

const IconBubble: React.FC<{component: ComponentSpec; style: React.CSSProperties; order: number}> = ({component, style, order}) => {
  const frame = useCurrentFrame();
  const {fps, width} = useVideoConfig();
  const {p, opacity} = entrance(frame, fps, order, 'pop');
  const size = clamp(width * 0.068, 58, 82);
  const iconSize = size * 0.48;
  const color = [orange, '#23684a', blue, '#e9832a'][order % 4];
  return (
    <div
      style={{
        position: 'absolute',
        ...style,
        opacity,
        transform: `translateY(${(1 - p) * 18}px) scale(${0.88 + p * 0.12})`,
        textAlign: 'center',
        color: ink,
        zIndex: 15 + order,
      }}
    >
      <div
        style={{
          width: size,
          height: size,
          borderRadius: '50%',
          border: '2px solid rgba(34,49,66,0.45)',
          background: 'rgba(255,252,244,0.92)',
          boxShadow: '4px 6px 0 rgba(34,49,66,0.1)',
          margin: '0 auto 12px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {component.icon ? (
          <Icon name={component.icon} size={iconSize} color={color} strokeWidth={2.6} />
        ) : (
          <DefaultBubbleIcon index={order} size={iconSize} color={color} />
        )}
      </div>
      <div style={{fontSize: clamp(width * 0.019, 20, 30), fontWeight: 700, lineHeight: 1.2}}>
        {compactText(component.text || '能力项', 10)}
      </div>
    </div>
  );
};

const DefaultBubbleIcon: React.FC<{index: number; size: number; color: string}> = ({index, size, color}) => {
  const icons = [Settings2, Palette, Wrench, FileText, Code2, Monitor, Check];
  const BubbleIcon = icons[index % icons.length];
  return <BubbleIcon size={size} color={color} strokeWidth={2.5} />;
};

const Subtitle: React.FC<{text?: string; isPortrait: boolean}> = ({text, isPortrait}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const {p, opacity} = entrance(frame, fps, 1.5, 'soft');
  const lines = wrapText(text, isPortrait ? 18 : 31, isPortrait ? 3 : 2);
  if (!text) return null;
  return (
    <div
      style={{
        position: 'absolute',
        left: width * (isPortrait ? 0.07 : 0.18),
        right: width * (isPortrait ? 0.07 : 0.18),
        bottom: height * (isPortrait ? 0.065 : 0.06),
        color: '#fff',
        fontSize: clamp(width * (isPortrait ? 0.043 : 0.027), 30, 44),
        fontWeight: 900,
        lineHeight: 1.2,
        textAlign: 'center',
        WebkitTextStroke: '5px #111',
        paintOrder: 'stroke fill',
        opacity,
        transform: `translateY(${(1 - p) * 14}px)`,
        zIndex: 40,
      }}
    >
      {lines.map((line, index) => (
        <div key={`${line}_${index}`}>{line}</div>
      ))}
    </div>
  );
};

const inferSketchLayout = (scene: RemotionSceneSpec): SceneLayout => {
  const text = `${scene.headline} ${scene.subtitle} ${scene.components.map((item) => item.text).join(' ')}`.toLowerCase();
  const nonArrow = scene.components.filter((item) => item.type !== 'arrow' && item.type !== 'badge');
  if (scene.layout && scene.layout !== 'auto') return scene.layout;
  if (text.includes(' vs ') || text.includes('对比') || text.includes('不是') || scene.components.some((item) => item.motion === 'strike')) return 'vs_compare';
  if (nonArrow.length >= 4) return 'icon_grid';
  return 'statement_highlight';
};

const buildFallbackCards = (scene: Partial<RemotionSceneSpec>): ComponentSpec[] => {
  const parts = splitParts(scene.visual || scene.subtitle || scene.headline).slice(0, 4);
  if (parts.length > 0) {
    return parts.map((part, index) => ({
      id: `fallback_${index}`,
      type: 'card',
      slot: 'center',
      text: part,
      variant: index === parts.length - 1 ? 'success' : 'default',
      motion: 'pop',
      icon: index === parts.length - 1 ? 'check' : 'sparkles',
    }));
  }
  return [
    {id: 'fallback_a', type: 'card', slot: 'left_top', text: '输入', variant: 'default', motion: 'pop', icon: 'message'},
    {id: 'fallback_b', type: 'card', slot: 'center', text: '理解', variant: 'warning', motion: 'pop', icon: 'brain'},
    {id: 'fallback_c', type: 'card', slot: 'right_top', text: '结果', variant: 'success', motion: 'pop', icon: 'check'},
  ];
};

export const SketchCourseScene: React.FC<{scene: RemotionSceneSpec}> = ({scene}) => {
  const {width, height} = useVideoConfig();
  const isPortrait = height >= width;
  const layout = inferSketchLayout(scene);
  const components = scene.components.length ? scene.components : buildFallbackCards(scene);
  const mainComponents = components.filter((item) => item.type !== 'arrow' && item.type !== 'background_pattern' && !(item.type === 'badge' && item.slot !== 'caption'));
  const badges = components.filter((item) => item.type === 'badge' && item.slot !== 'caption');
  const safeTop = isPortrait ? height * 0.18 : height * 0.19;
  const safeBottom = isPortrait ? height * 0.2 : height * 0.18;

  return (
    <div style={{width: '100%', height: '100%', position: 'relative', overflow: 'hidden', fontFamily: '"Microsoft YaHei", "PingFang SC", Arial, sans-serif'}}>
      <PaperBackground />
      <TopHeader scene={scene} isPortrait={isPortrait} />
      {badges[0] ? <BadgeRibbon component={badges[0]} isPortrait={isPortrait} /> : null}
      {layout === 'icon_grid' ? (
        <IconGrid scene={scene} components={mainComponents} safeTop={safeTop} safeBottom={safeBottom} isPortrait={isPortrait} />
      ) : layout === 'vs_compare' || layout === 'two_column_compare' ? (
        <VsCompare components={mainComponents} safeTop={safeTop} isPortrait={isPortrait} />
      ) : layout === 'three_step_flow' || layout === 'vertical_flow' ? (
        <ThreeStepFlow components={mainComponents} safeTop={safeTop} safeBottom={safeBottom} isPortrait={isPortrait} />
      ) : (
        <StatementHighlight scene={scene} components={mainComponents} safeTop={safeTop} isPortrait={isPortrait} />
      )}
      <Subtitle text={scene.subtitle} isPortrait={isPortrait} />
    </div>
  );
};

const BadgeRibbon: React.FC<{component: ComponentSpec; isPortrait: boolean}> = ({component, isPortrait}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const {p, opacity} = entrance(frame, fps, 0.8, 'draw');
  return (
    <div
      style={{
        position: 'absolute',
        top: height * (isPortrait ? 0.135 : 0.145),
        left: width * 0.5 - width * (isPortrait ? 0.28 : 0.18),
        width: width * (isPortrait ? 0.56 : 0.36),
        height: 3,
        background: `linear-gradient(90deg, transparent, rgba(242,169,59,${opacity}), transparent)`,
        transform: `scaleX(${p})`,
        transformOrigin: 'center',
      }}
    >
      <div
        style={{
          position: 'absolute',
          top: -18,
          left: 0,
          right: 0,
          color: orange,
          fontWeight: 800,
          textAlign: 'center',
          fontSize: clamp(width * 0.016, 16, 24),
        }}
      >
        {compactText(component.text || '实战场景', 18)}
      </div>
    </div>
  );
};

const IconGrid: React.FC<{scene: RemotionSceneSpec; components: ComponentSpec[]; safeTop: number; safeBottom: number; isPortrait: boolean}> = ({scene, components, safeTop, safeBottom, isPortrait}) => {
  const {width, height} = useVideoConfig();
  const items = (components.length ? components : buildFallbackCards({headline: '', subtitle: '', visual: '', components: []})).slice(0, 4);
  const titleW = width * (isPortrait ? 0.66 : 0.34);
  const titleH = height * 0.09;
  const top = safeTop + height * 0.03;
  const gridTop = top + titleH + height * 0.06;
  const gridW = width * (isPortrait ? 0.62 : 0.28);
  const cellW = gridW / 2;
  const cellH = (height - gridTop - safeBottom) / 2;

  return (
    <>
      <SketchCard
        component={{id: 'orange_title', type: 'card', slot: 'center', text: scene.visual || scene.headline || '核心要点', variant: 'warning', motion: 'pop'}}
        order={1}
        tone="orange"
        style={{left: (width - titleW) / 2, top, width: titleW, height: titleH}}
      />
      {items.map((component, index) => (
        <IconBubble
          key={component.id}
          component={component}
          order={index + 2}
          style={{
            left: (width - gridW) / 2 + (index % 2) * cellW,
            top: gridTop + Math.floor(index / 2) * cellH,
            width: cellW,
            height: cellH * 0.72,
          }}
        />
      ))}
    </>
  );
};

const VsCompare: React.FC<{components: ComponentSpec[]; safeTop: number; isPortrait: boolean}> = ({components, safeTop, isPortrait}) => {
  const {width, height} = useVideoConfig();
  const cards = components.length >= 2 ? components : buildFallbackCards({headline: '', subtitle: '', visual: '', components: []});
  const left = cards[0];
  const right = cards[1] ?? cards[0];
  const cardW = width * (isPortrait ? 0.34 : 0.23);
  const cardH = height * (isPortrait ? 0.085 : 0.1);
  const gap = width * (isPortrait ? 0.08 : 0.12);
  const top = safeTop + height * 0.035;
  const centerX = width / 2;

  return (
    <>
      <SketchCard component={left} order={1} style={{left: centerX - gap / 2 - cardW, top, width: cardW, height: cardH}} />
      <SketchCard component={right} order={2} style={{left: centerX + gap / 2, top, width: cardW, height: cardH}} />
      <div
        style={{
          position: 'absolute',
          top: top + cardH * 0.34,
          left: centerX - 28,
          width: 56,
          color: orange,
          fontSize: clamp(width * 0.03, 26, 42),
          fontWeight: 900,
          textAlign: 'center',
          zIndex: 25,
        }}
      >
        vs
      </div>
      {components[2]?.text ? (
        <StatementStrip text={components[2].text} order={3} top={top + cardH + height * 0.07} />
      ) : null}
      {components.slice(4, 7).map((component, index) => (
        <MiniNote
          key={component.id}
          component={component}
          order={index + 4.4}
          style={{
            left: width * (isPortrait ? 0.13 + index * 0.24 : 0.3 + index * 0.14),
          top: top + cardH + height * (components[2]?.text ? 0.245 : 0.13),
            width: width * (isPortrait ? 0.22 : 0.12),
          }}
        />
      ))}
      <SketchCard
        component={components[3] ?? {id: 'result', type: 'card', slot: 'bottom', text: components[2]?.text || '关键组合', variant: 'warning', motion: 'pop', icon: ''}}
        order={4}
        tone="orange"
        style={{
          left: width * (isPortrait ? 0.16 : 0.36),
          top: top + cardH + height * (components[2]?.text ? 0.15 : 0.08),
          width: width * (isPortrait ? 0.68 : 0.28),
          height: height * 0.09,
        }}
      />
    </>
  );
};

const MiniNote: React.FC<{component: ComponentSpec; order: number; style: React.CSSProperties}> = ({component, order, style}) => {
  const frame = useCurrentFrame();
  const {fps, width} = useVideoConfig();
  const {p, opacity} = entrance(frame, fps, order, 'pop');
  return (
    <div
      style={{
        position: 'absolute',
        ...style,
        opacity,
        transform: `translateY(${(1 - p) * 12}px) rotate(${(seedFromId(component.id) - 0.5) * 3}deg)`,
        padding: '8px 12px',
        borderRadius: 999,
        border: '2px solid rgba(34,49,66,0.28)',
        background: 'rgba(255,250,239,0.82)',
        color: muted,
        fontSize: clamp(width * 0.014, 15, 22),
        fontWeight: 750,
        textAlign: 'center',
        boxShadow: '3px 4px 0 rgba(34,49,66,0.08)',
        zIndex: 28,
      }}
    >
      {compactText(component.text, 8)}
    </div>
  );
};

const StatementStrip: React.FC<{text: string; order: number; top: number}> = ({text, order, top}) => {
  const frame = useCurrentFrame();
  const {fps, width} = useVideoConfig();
  const {p, opacity} = entrance(frame, fps, order, 'soft');
  return (
    <div
      style={{
        position: 'absolute',
        left: width * 0.24,
        right: width * 0.24,
        top,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        gap: 18,
        opacity,
        transform: `translateY(${(1 - p) * 14}px)`,
        zIndex: 20,
      }}
    >
      <span style={{width: 6, height: 44, borderRadius: 99, background: orange}} />
      <span style={{fontSize: clamp(width * 0.026, 24, 36), color: ink, fontWeight: 750}}>{compactText(text, 22)}</span>
    </div>
  );
};

const ThreeStepFlow: React.FC<{components: ComponentSpec[]; safeTop: number; safeBottom: number; isPortrait: boolean}> = ({components, safeTop, safeBottom, isPortrait}) => {
  const {width, height} = useVideoConfig();
  const cards = components.length >= 3 ? components.slice(0, 3) : buildFallbackCards({headline: '', subtitle: '', visual: '', components: []});
  const extras = components.slice(3, 6);
  if (isPortrait) {
    const cardW = width * 0.68;
    const cardH = height * 0.105;
    const startTop = safeTop + height * 0.03;
    const step = (height - safeBottom - startTop - cardH) / 2;
    return (
      <>
        {cards.map((component, index) => (
          <React.Fragment key={component.id}>
            <SketchCard
              component={component}
              order={index + 1}
              tone={index === cards.length - 1 ? 'green' : 'paper'}
              style={{left: (width - cardW) / 2, top: startTop + index * step, width: cardW, height: cardH}}
            />
          </React.Fragment>
        ))}
        {extras.map((component, index) => (
          <MiniNote
            key={component.id}
            component={component}
            order={index + 5}
            style={{left: width * (0.17 + index * 0.22), top: height - safeBottom + height * 0.01, width: width * 0.18}}
          />
        ))}
      </>
    );
  }

  const cardW = width * 0.24;
  const cardH = height * 0.19;
  const gap = width * 0.06;
  const totalW = cardW * 3 + gap * 2;
  const top = safeTop + height * 0.06;
  const left = (width - totalW) / 2;
  return (
    <>
      {cards.map((component, index) => (
        <React.Fragment key={component.id}>
          <SketchCard
            component={component}
            order={index + 1}
            tone={index === cards.length - 1 ? 'green' : 'paper'}
            style={{left: left + index * (cardW + gap), top, width: cardW, height: cardH}}
          />
        </React.Fragment>
      ))}
      {extras.map((component, index) => (
        <MiniNote
          key={component.id}
          component={component}
          order={index + 5}
          style={{left: left + index * (cardW + gap), top: top + cardH + height * 0.045, width: cardW}}
        />
      ))}
    </>
  );
};

const StatementHighlight: React.FC<{scene: RemotionSceneSpec; components: ComponentSpec[]; safeTop: number; isPortrait: boolean}> = ({scene, components, safeTop, isPortrait}) => {
  const {width, height} = useVideoConfig();
  const text = components[0]?.text || scene.headline || scene.subtitle || '关键结论';
  const note = scene.visual || components[1]?.text || '';
  return (
    <>
      {note ? <StatementStrip text={note} order={1} top={safeTop + height * 0.03} /> : null}
      <SketchCard
        component={{...(components[0] ?? {id: 'statement', type: 'card', slot: 'center', variant: 'warning', motion: 'pop'}), text}}
        order={2}
        tone="orange"
        style={{
          left: width * (isPortrait ? 0.12 : 0.32),
          top: safeTop + height * (note ? 0.16 : 0.06),
          width: width * (isPortrait ? 0.76 : 0.36),
          height: height * (isPortrait ? 0.12 : 0.13),
        }}
      />
    </>
  );
};
