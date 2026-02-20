/// <reference types="vite/client" />

// Type shim for plotly.js-dist-min which ships without its own declaration file
declare module 'plotly.js-dist-min' {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const Plotly: any
  export default Plotly
  export = Plotly
}
