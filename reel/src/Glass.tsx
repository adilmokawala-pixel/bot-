import React, {createContext, useContext} from 'react';
import {interpolate, useCurrentFrame} from 'remotion';

/** true while the cream (light) scene is on screen: light glass would be unreadable there, so it turns dark. */
export const OnLightBg = createContext(false);

/** A light sweep that crosses the panel once, starting at `from` (frame). */
export const Sheen: React.FC<{from: number; radius: number; duration?: number}> = ({from, radius, duration = 16}) => {
	const frame = useCurrentFrame();
	const x = interpolate(frame - from, [0, duration], [-60, 160], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	if (frame - from > duration || frame < from) return null;
	return (
		<div style={{position: 'absolute', inset: 0, borderRadius: radius, overflow: 'hidden', pointerEvents: 'none'}}>
			<div
				style={{
					position: 'absolute',
					top: '-20%',
					bottom: '-20%',
					left: `${x}%`,
					width: '28%',
					transform: 'skewX(-20deg)',
					background: 'linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.35) 50%, rgba(255,255,255,0) 100%)',
				}}
			/>
		</div>
	);
};

type GlassProps = {
	tone: 'dark' | 'light';
	radius: number;
	style?: React.CSSProperties;
	sheenFrom?: number;
	children?: React.ReactNode;
};

/** Frosted glass panel with bevel. dark = captions, light = annotations. */
export const Glass: React.FC<GlassProps> = ({tone, radius, style, sheenFrom, children}) => {
	const onLight = useContext(OnLightBg);
	const dark = tone === 'dark' || onLight;
	return (
		<div
			style={{
				position: 'relative',
				borderRadius: radius,
				background: dark ? 'rgba(12,12,12,0.42)' : 'rgba(255,255,255,0.16)',
				backdropFilter: 'blur(22px) saturate(170%)',
				WebkitBackdropFilter: 'blur(22px) saturate(170%)',
				border: `2px solid rgba(255,255,255,${dark ? 0.42 : 0.5})`,
				boxShadow: [
					'inset 0 2px 0 rgba(255,255,255,0.55)',
					'inset 0 -2px 6px rgba(0,0,0,0.18)',
					'0 18px 40px rgba(0,0,0,0.28)',
				].join(', '),
				...style,
			}}
		>
			{children}
			{sheenFrom !== undefined ? <Sheen from={sheenFrom} radius={radius} /> : null}
		</div>
	);
};

/** Small glass square used in backgrounds (optionally blurred for depth of field). */
export const GlassSquare: React.FC<{size: number; x: number; y: number; rot: number; blur?: number; children?: React.ReactNode}> = ({
	size,
	x,
	y,
	rot,
	blur = 0,
	children,
}) => (
	<div
		style={{
			position: 'absolute',
			left: x - size / 2,
			top: y - size / 2,
			width: size,
			height: size,
			borderRadius: size * 0.22,
			transform: `rotate(${rot}deg)`,
			background: 'linear-gradient(135deg, rgba(255,255,255,0.28), rgba(255,255,255,0.08))',
			border: '2px solid rgba(255,255,255,0.35)',
			boxShadow: 'inset 0 2px 0 rgba(255,255,255,0.5), 0 20px 40px rgba(0,0,0,0.18)',
			backdropFilter: 'blur(10px)',
			filter: blur ? `blur(${blur}px)` : undefined,
			display: 'flex',
			alignItems: 'center',
			justifyContent: 'center',
			fontSize: size * 0.48,
		}}
	>
		{children}
	</div>
);
