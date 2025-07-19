/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./src/**/*.{html,ts}",
    ],
    // Habilitamos el modo oscuro para que funcione con tu selector [data-theme="dark"]
    darkMode: ['selector', '[data-theme="dark"]'],
    theme: {
        extend: {
            // ==========================================================================
            // COLORES OPTIMIZADOS
            // ==========================================================================
            colors: {
                // Colores semánticos mejorados
                border: "hsl(var(--border))",
                input: "hsl(var(--input))",
                ring: "hsl(var(--ring))",
                background: "hsl(var(--background))",
                foreground: "hsl(var(--foreground))",
                card: {
                    DEFAULT: "hsl(var(--card))",
                    foreground: "hsl(var(--card-foreground))",
                },
                primary: {
                    DEFAULT: "hsl(var(--primary))",
                    foreground: "hsl(var(--primary-foreground))",
                    50: "hsl(var(--gold-50))",
                    100: "hsl(var(--gold-100))",
                    200: "hsl(var(--gold-200))",
                    300: "hsl(var(--gold-300))",
                    400: "hsl(var(--gold-400))",
                    500: "hsl(var(--gold-500))",
                    600: "hsl(var(--gold-600))",
                    700: "hsl(var(--gold-700))",
                    800: "hsl(var(--gold-800))",
                    900: "hsl(var(--gold-900))",
                    950: "hsl(var(--gold-950))",
                },
                secondary: {
                    DEFAULT: "hsl(var(--secondary))",
                    foreground: "hsl(var(--secondary-foreground))",
                    50: "hsl(var(--red-50))",
                    100: "hsl(var(--red-100))",
                    200: "hsl(var(--red-200))",
                    300: "hsl(var(--red-300))",
                    400: "hsl(var(--red-400))",
                    500: "hsl(var(--red-500))",
                    600: "hsl(var(--red-600))",
                    700: "hsl(var(--red-700))",
                    800: "hsl(var(--red-800))",
                    900: "hsl(var(--red-900))",
                    950: "hsl(var(--red-950))",
                },
                accent: {
                    DEFAULT: "hsl(var(--accent))",
                    foreground: "hsl(var(--accent-foreground))",
                    50: "hsl(var(--green-50))",
                    100: "hsl(var(--green-100))",
                    200: "hsl(var(--green-200))",
                    300: "hsl(var(--green-300))",
                    400: "hsl(var(--green-400))",
                    500: "hsl(var(--green-500))",
                    600: "hsl(var(--green-600))",
                    700: "hsl(var(--green-700))",
                    800: "hsl(var(--green-800))",
                    900: "hsl(var(--green-900))",
                    950: "hsl(var(--green-950))",
                },
                destructive: {
                    DEFAULT: "hsl(var(--destructive))",
                    foreground: "hsl(var(--destructive-foreground))",
                },
                muted: {
                    DEFAULT: "hsl(var(--muted))",
                    foreground: "hsl(var(--muted-foreground))",
                },
                warning: {
                    DEFAULT: "hsl(var(--warning))",
                    foreground: "hsl(var(--warning-foreground))",
                },
                success: {
                    DEFAULT: "hsl(var(--success))",
                    foreground: "hsl(var(--success-foreground))",
                },
                info: {
                    DEFAULT: "hsl(var(--info))",
                    foreground: "hsl(var(--info-foreground))",
                },
                // Colores de marca MR. DÓLAR
                "mr-dollar-gold": "hsl(var(--gold-500))",
                "mr-dollar-red": "hsl(var(--red-500))",
                "mr-dollar-green": "hsl(var(--green-500))",
                "mr-dollar-chef-hat": "hsl(0 0% 100%)",
                "mr-dollar-outline": "hsl(0 0% 0%)",
            },
            // ==========================================================================
            // TOKENS DE DISEÑO MEJORADOS
            // ==========================================================================
            borderRadius: {
                xs: "0.125rem",
                sm: "0.25rem",
                DEFAULT: "0.5rem",
                md: "0.75rem",
                lg: "1rem",
                xl: "1.25rem",
                "2xl": "1.5rem",
                "3xl": "2rem",
                "4xl": "2.5rem",
                full: "9999px",
            },
            boxShadow: {
                modern: "var(--drop-shadow-modern)",
                elevated: "var(--drop-shadow-elevated)",
                floating: "var(--drop-shadow-floating)",
                "glow-soft": "var(--drop-shadow-glow-soft)",
                "glow-intense": "var(--drop-shadow-glow-intense)",
            },
            dropShadow: {
                modern: "var(--drop-shadow-modern)",
                elevated: "var(--drop-shadow-elevated)",
                floating: "var(--drop-shadow-floating)",
                "glow-soft": "var(--drop-shadow-glow-soft)",
                "glow-intense": "var(--drop-shadow-glow-intense)",
            },
            transitionDuration: {
                instant: "0ms",
                fast: "100ms",
                subtle: "150ms",
                moderate: "300ms",
                slow: "500ms",
                slower: "750ms",
            },
            transitionTimingFunction: {
                natural: "cubic-bezier(0.4, 0, 0.2, 1)",
                bounce: "cubic-bezier(0.68, -0.55, 0.265, 1.55)",
                smooth: "cubic-bezier(0.25, 0.46, 0.45, 0.94)",
                "ease-out-back": "cubic-bezier(0.34, 1.56, 0.64, 1)",
                "ease-in-out-back": "cubic-bezier(0.68, -0.6, 0.32, 1.6)",
            },
            spacing: {
                xs: "0.25rem",
                sm: "0.5rem",
                md: "1rem",
                lg: "1.5rem",
                xl: "2rem",
                "2xl": "3rem",
                "3xl": "4rem",
                "4xl": "5rem",
                "5xl": "6rem",
            },
            fontSize: {
                xs: ["0.75rem", { lineHeight: "1rem" }],
                sm: ["0.875rem", { lineHeight: "1.25rem" }],
                base: ["1rem", { lineHeight: "1.5rem" }],
                lg: ["1.125rem", { lineHeight: "1.75rem" }],
                xl: ["1.25rem", { lineHeight: "1.75rem" }],
                "2xl": ["1.5rem", { lineHeight: "2rem" }],
                "3xl": ["1.875rem", { lineHeight: "2.25rem" }],
                "4xl": ["2.25rem", { lineHeight: "2.5rem" }],
                "5xl": ["3rem", { lineHeight: "1" }],
                "6xl": ["3.75rem", { lineHeight: "1" }],
            },
            fontWeight: {
                thin: "100",
                extralight: "200",
                light: "300",
                normal: "400",
                medium: "500",
                semibold: "600",
                bold: "700",
                extrabold: "800",
                black: "900",
            },
            zIndex: {
                dropdown: "1000",
                sticky: "1020",
                fixed: "1030",
                "modal-backdrop": "1040",
                modal: "1050",
                popover: "1060",
                tooltip: "1070",
                toast: "1080",
                max: "9999",
            },
            screens: {
                xs: "30rem",
            },
            // ==========================================================================
            // ANIMACIONES MEJORADAS
            // ==========================================================================
            keyframes: {
                "bounce-in-modern": {
                    "0%": { opacity: "0", transform: "scale(0.3) translateY(30px)" },
                    "50%": { opacity: "1", transform: "scale(1.05) translateY(-10px)" },
                    "70%": { transform: "scale(0.95) translateY(5px)" },
                    "100%": { opacity: "1", transform: "scale(1) translateY(0)" },
                },
                "pulse-glow-modern": {
                    "0%, 100%": { boxShadow: "var(--drop-shadow-modern), var(--drop-shadow-glow-soft)" },
                    "50%": { boxShadow: "var(--drop-shadow-elevated), var(--drop-shadow-glow-intense)" },
                },
                "slide-in-right": {
                    from: { opacity: "0", transform: "translateX(30px)" },
                    to: { opacity: "1", transform: "translateX(0)" },
                },
                "slide-in-left": {
                    from: { opacity: "0", transform: "translateX(-30px)" },
                    to: { opacity: "1", transform: "translateX(0)" },
                },
                "scale-in": {
                    from: { opacity: "0", transform: "scale(0.9)" },
                    to: { opacity: "1", transform: "scale(1)" },
                },
                shimmer: {
                    "0%": { backgroundPosition: "-200% 0" },
                    "100%": { backgroundPosition: "200% 0" },
                },
                "float-gentle": {
                    "0%, 100%": { transform: "translateY(0)" },
                    "50%": { transform: "translateY(-8px)" },
                },
                "fade-in": {
                    from: { opacity: "0" },
                    to: { opacity: "1" },
                },
                "slide-down": {
                    from: { opacity: "0", transform: "translateY(-10px)" },
                    to: { opacity: "1", transform: "translateY(0)" },
                },
                "slide-up": {
                    from: { opacity: "0", transform: "translateY(10px)" },
                    to: { opacity: "1", transform: "translateY(0)" },
                },
            },
            animation: {
                "bounce-in-modern": "bounce-in-modern 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55)",
                "slide-in-right": "slide-in-right 0.4s ease-out",
                "slide-in-left": "slide-in-left 0.4s ease-out",
                "scale-in": "scale-in 0.3s ease-out",
                "float-gentle": "float-gentle 4s ease-in-out infinite",
                "pulse-glow-modern": "pulse-glow-modern 2s ease-in-out infinite",
                shimmer: "shimmer 2s infinite",
                "fade-in": "fade-in 0.2s ease-out",
                "slide-down": "slide-down 0.3s ease-out",
                "slide-up": "slide-up 0.3s ease-out",
            },
            // ==========================================================================
            // GRADIENTES MEJORADOS
            // ==========================================================================
            backgroundImage: {
                "gradient-primary": "var(--gradient-primary)",
                "gradient-secondary": "var(--gradient-secondary)",
                "gradient-accent": "var(--gradient-accent)",
                "gradient-background": "var(--gradient-background)",
                "shimmer-gradient": "linear-gradient(90deg, transparent 25%, hsl(var(--primary) / 0.1) 50%, transparent 75%)",
            },
            backdropBlur: {
                xs: "2px",
                sm: "4px",
                md: "8px",
                lg: "16px",
                xl: "24px",
                "2xl": "40px",
            },
            aspectRatio: {
                "4/3": "4 / 3",
                "3/2": "3 / 2",
                "5/4": "5 / 4",
            },
        },
    },
    plugins: [],
}
