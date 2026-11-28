import fs from 'node:fs';
export function loadEnvironment(file=new URL('../.env.local',import.meta.url)){
 try{for(const line of fs.readFileSync(file,'utf8').split(/\r?\n/)){const m=/^([A-Z_][A-Z0-9_]*)=(.*)$/.exec(line.trim());if(m&&!process.env[m[1]])process.env[m[1]]=m[2].replace(/^(['"])(.*)\1$/,'$2')}}catch(e){if(e.code!=='ENOENT')throw e}
}
