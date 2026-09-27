export type Bg = 'original' | 'orange' | 'dark' | 'light' | 'image';

export type Word = {w: string; start: number; end: number};

export type CaptionGroup = {
	/** indexes into Timeline.words (max 3) */
	words: number[];
	start: number;
	end: number;
	/** English line (UPPERCASE, «keyword» highlighted) */
	en: string;
};

export type Scene = {
	start: number;
	end: number;
	bg: Bg;
	/** orange scene: giant keyword sliding behind the head */
	keyword?: string;
	/** dark scene: icons in glass squares */
	icons?: string[];
	/** light scene: path labels, e.g. ["الفكرة","الملف","التمويل","المشروع"] */
	path?: string[];
	/** image scene: illustration behind the person, path relative to public/ */
	image?: string;
	/** image scene: short glass label on the picture */
	label?: string;
};

export type Push = {start: number; end: number};

export type Annotation =
	| {type: 'chip'; start: number; end: number; text: string; emoji: string}
	| {type: 'chips2'; start: number; end: number; items: {text: string; emoji: string}[]}
	| {type: 'comment'; start: number; end: number; typeStart: number; typeEnd: number; text: string}
	| {type: 'dm'; start: number; end: number}
	| {type: 'checklist'; start: number; end: number; items: string[]}
	| {type: 'tiles'; start: number; end: number; items: {text: string; emoji: string}[]; active: number}
	| {type: 'cta'; start: number; end: number; text: string}
	| {type: 'card'; start: number; end: number; title: string; sub?: string; image?: string; emoji?: string};

export type Sfx = {name: string; at: number; volume: number};

export type Timeline = {
	id: string;
	fps: number;
	durationInFrames: number;
	video: {src: string; alpha: string; width: number; height: number};
	voice: string;
	/** jump-cut segments in output seconds */
	segments: {start: number; end: number}[];
	words: Word[];
	captions: CaptionGroup[];
	scenes: Scene[];
	pushes: Push[];
	annotations: Annotation[];
	sfx: Sfx[];
	music: {src: string; volume: number};
};
