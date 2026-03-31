type ToastOptions = {
    title?: string
    description?: string
    type?: "success" | "error" | "info"
}

export const toaster = {
    create: (opts: ToastOptions) => {
        // Minimal placeholder — replace with a proper UI toast library in production.
        if (import.meta.env.DEV) {
            // eslint-disable-next-line no-console
            console.log("TOAST", opts.title, opts.description, opts.type)
        }
    },
}

export default toaster
