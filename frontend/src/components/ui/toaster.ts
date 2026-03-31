import { logger } from '@/lib/logger'

type ToastOptions = {
    title?: string
    description?: string
    type?: "success" | "error" | "info"
}

export const toaster = {
    create: (opts: ToastOptions) => {
        // Minimal placeholder — replace with a proper UI toast library in production.
        if (import.meta.env.DEV) {
            logger.info("TOAST", opts.title, opts.description, opts.type)
        }
    },
}

export default toaster
