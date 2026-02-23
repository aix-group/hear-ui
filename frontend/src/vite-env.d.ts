/// <reference types="vite/client" />

// Type shim for plotly.js-dist-min which ships without its own declaration file
declare module 'plotly.js-dist-min' {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  export type Data = Record<string, any>
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  export type Layout = Record<string, any>
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  export type Config = Record<string, any>
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  export type Annotations = Array<Record<string, any>>
  export function react(
    div: HTMLElement | string | null,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    data: any[],
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    layout?: any,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    config?: any,
  ): Promise<void>
  export function purge(div: HTMLElement | string | null): void
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const Plotly: any
  export default Plotly
}
