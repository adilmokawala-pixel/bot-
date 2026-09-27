import {Config} from '@remotion/cli/config';

Config.setEntryPoint('./src/index.ts');
Config.setVideoImageFormat('jpeg');
Config.setJpegQuality(95);
Config.setCodec('h264');
Config.setCrf(16);
Config.setPixelFormat('yuv420p');
Config.setAudioBitrate('320k');
Config.setConcurrency(4);
