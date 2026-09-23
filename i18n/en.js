window.I18N = window.I18N || {};
// Ingles -- a lingua da raiz do site. Serve de REFERENCIA: um dicionario novo
// tem de ter exactamente estas chaves, nem mais nem menos.
//
// O que NAO esta aqui, de proposito:
//   * o log de arranque e o terminal CRT (app.js) -- sao comandos de shell e
//     saida de maquina; um boot log em portugues era mais estranho, nao mais
//     claro. Mesma decisao que o mock-up de log do LogViewer, que fica sempre
//     da esquerda para a direita;
//   * a divisa "developing practical solutions for small planetary systems" --
//     e a assinatura da casa e fica em ingles em todo o lado, incluindo nos 15
//     dicionarios do LogViewer;
//   * a notacao dos instrumentos (OBJ-001, CLASS M, AU, RAD/S, as coordenadas,
//     MMXXVI, VOL. I) -- sao marcacoes, nao lingua.
window.I18N.en = {
  "meta.title": "mBrothers // Developing practical solutions for small planetary systems",
  "meta.desc": "mBrothers builds quiet, practical software for small planetary systems. Home of The Absolute LogViewer and ExplorerFocus.",
  "og.title": "mBrothers — Developing practical solutions for small planetary systems",
  "og.desc": "A small software studio building quiet, practical instruments. No subscriptions, no telemetry — tools that do one thing carefully and get out of the way.",
  "og.imgalt": "mBrothers — a ringed planet beside the studio wordmark.",
  "tw.title": "mBrothers — small planetary systems",
  "tw.desc": "Quiet, practical software. Home of The Absolute LogViewer and ExplorerFocus.",
  "ld.desc": "An independent software studio building quiet, practical instruments for small planetary systems.",

  "boot.hint": "click or press any key to skip",
  "skip.link": "Skip to content",
  "theme.toggle": "Toggle day / night",
  "lang.label": "Language",

  "nav.products": "Products",
  "nav.philosophy": "Philosophy",
  "nav.contact": "Transmission",

  "hero.vol": "VOL. I · MMXXVI",
  "hero.signal": "SIGNAL ACQUIRED",
  "hero.place": "LISBON · 38.7°N 9.1°W",
  "hud.feed": "LIVE FEED · ORBIT CAM 04",
  "hud.obj": "OBJ-001 / PLANET · CLASS M",
  "hud.signal": "SIGNAL : STABLE",
  "dl.temp": "SURFACE TEMP",
  "dl.atmo": "ATMOSPHERE",
  "dl.atmo.v": "N₂ · O₂ · TRACE",
  "dl.rot": "ROTATION",
  "dl.moon": "MOON · 1",
  "dl.moon.v": "PERIOD 30s",
  "grab.hint": "⟲ drag to rotate · move to look",
  "orn.est": "EST. 2026",

  "intro.label": "On the studio",
  "intro.p1": '<span class="drop">W</span>e are a small workshop of software craftspeople orbiting a quiet sun. Our concern is the everyday — the windows you keep open, the logs you stare at, the focus you keep losing. We build tools that earn their place on your desktop by being quiet, fast, and considerate.',
  "intro.p2": "No subscriptions to forget. No telemetry to dread. Just instruments that do one thing carefully, transmit nothing home, and then get out of the way.",

  "products.title": "The Catalogue",
  "status.ok": "Status · operational",
  "more": 'Read more <span class="arrow">→</span>',

  "p1.tag": "Observation · Forensics · Calm",
  "p1.desc": "A serene reader for log files of any size. Stream, filter, and follow without the editor stuttering. For when the system speaks and you actually need to listen.",
  "p2.tag": "Attention · File systems · Quiet",
  "p2.desc": "A focused Windows Explorer alternative — profiles, configurable trees, rich preview, honest file operations. Version 2 adds encrypted vaults that mount as a drive letter.",
  "p3.h": "In transmission",
  "p3.tag": "Forthcoming · 2026",
  "p3.desc": "Another small instrument is taking shape on the workbench. Built with the same patience and the same refusal to add what isn't needed.",
  "p3.status": "Status · incoming",
  "p3.cta": 'Be notified <span class="arrow">→</span>',
  "p4.h": "Reserved",
  "p4.tag": "An idea, still quiet",
  "p4.desc": "Space held open for the next solution worth building. The catalogue grows slowly — on purpose.",
  "p4.status": "Status · dormant",
  "p4.signal": "Signal · faint",

  "phil.quote": '"We make software the way an old workshop makes <span class="glow">instruments</span> —<br/>small in number, considered in detail, built to outlast the trend."',
  "phil.sig": "— the mBrothers",

  "foot.studio.h": "The Studio",
  "foot.studio.p": "mBrothers is an independent software studio. Two minds, a few good tools, and a long view of small worlds.",
  "foot.trans.h": "Transmission",
  "foot.prov.h": "Provenance",
  "foot.prov.p": "Hand-built in Lisbon.<br/>Hosted at nunex-mbrothers.github.io",
  "foot.set": "Set in Cormorant · Italianno · JetBrains Mono",
  "foot.views": "Page visits",

  "motion.full": "▸ full motion",
  "motion.calm": "motion · full",
  "motion.t.on": "Enable the full animated experience (overrides the system setting)",
  "motion.t.off": "Full motion on — click to follow the system setting again"
};
