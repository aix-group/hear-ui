import type {ApiError} from "./client"
import useCustomToast from "./hooks/useCustomToast"

export const emailPattern = {
    value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
    message: "Invalid email address",
}

export const namePattern = {
    value: /^[A-Za-z\s\u00C0-\u017F]{1,30}$/,
    message: "Invalid name",
}

export const passwordRules = (isRequired = true) => {
    const rules: any = {
        minLength: {
            value: 8,
            message: "Password must be at least 8 characters",
        },
    }

    if (isRequired) {
        rules.required = "Password is required"
    }

    return rules
}

export const confirmPasswordRules = (
    getValues: () => any,
    isRequired = true,
) => {
    const rules: any = {
        validate: (value: string) => {
            const password = getValues().password || getValues().new_password
            return value === password ? true : "The passwords do not match"
        },
    }

    if (isRequired) {
        rules.required = "Password confirmation is required"
    }

    return rules
}

export const handleError = (err: ApiError) => {
    const {showErrorToast} = useCustomToast()
    const errDetail = (err.body as Record<string, unknown>)?.detail
    let errorMessage = errDetail || "Something went wrong."
    if (Array.isArray(errDetail) && errDetail.length > 0) {
        errorMessage = errDetail[0].msg
    }
    showErrorToast(errorMessage)
}

/** Returns the English ordinal suffix for a day number (1→"st", 2→"nd", 3→"rd", else "th"). */
function _dayOrdinal(n: number): string {
    if (n >= 11 && n <= 13) return 'th'
    switch (n % 10) {
        case 1: return 'st'
        case 2: return 'nd'
        case 3: return 'rd'
        default: return 'th'
    }
}

/**
 * Formats a birth-date string for display.
 * - English  → American format: "May 16th, 2026"
 * - German   → European format: "16.05.2026"
 *
 * Accepts either "YYYY-MM-DD" (ISO) or "DD.MM.YYYY" (German) as input.
 */
export function formatBirthDateLocale(raw: string | null | undefined, language: string): string | null {
    if (!raw) return null

    let year: string, month: string, day: string

    if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) {
        ;[year, month, day] = raw.split('-')
    } else if (/^\d{2}\.\d{2}\.\d{4}$/.test(raw)) {
        const parts = raw.split('.')
        day = parts[0]
        month = parts[1]
        year = parts[2]
    } else {
        return raw
    }

    if (language.startsWith('en')) {
        const monthNames = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December',
        ]
        const monthIndex = parseInt(month, 10) - 1
        const dayNum = parseInt(day, 10)
        const monthName = monthNames[monthIndex] ?? month
        return `${monthName} ${dayNum}${_dayOrdinal(dayNum)}, ${year}`
    }

    return `${day}.${month}.${year}`
}
