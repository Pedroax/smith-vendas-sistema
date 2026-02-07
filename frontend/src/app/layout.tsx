import "@/lib/setup-fetch"; // DEVE SER O PRIMEIRO IMPORT - Interceptor de fetch global
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ClientProviders } from "@/components/ClientProviders";
import { LayoutWrapper } from "@/components/LayoutWrapper";
import { ClientInit } from "./_client-init";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Smith 2.0 - Portal de Projetos",
  description: "Portal de acompanhamento de projetos para clientes e administradores",
  manifest: "/manifest.json",
  themeColor: "#3b82f6",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "Smith Portal",
  },
  formatDetection: {
    telephone: false,
  },
  openGraph: {
    type: "website",
    siteName: "Smith 2.0",
    title: "Smith 2.0 - Portal de Projetos",
    description: "Portal de acompanhamento de projetos para clientes e administradores",
  },
  twitter: {
    card: "summary",
    title: "Smith 2.0 - Portal de Projetos",
    description: "Portal de acompanhamento de projetos para clientes e administradores",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                if (typeof window === 'undefined') return;

                const originalFetch = window.fetch;

                window.fetch = function(input, init) {
                  let modifiedInput = input;
                  let urlString = typeof input === 'string' ? input : (input instanceof Request ? input.url : input.href);

                  console.log('🚨 [INLINE-SCRIPT] Interceptou:', urlString);

                  if (typeof input === 'string' && input.includes('railway.app') && input.startsWith('http://')) {
                    modifiedInput = input.replace('http://', 'https://');
                    console.log('🔒 [INLINE-SCRIPT] CORRIGIDO:', modifiedInput);
                  } else if (input instanceof Request && input.url.includes('railway.app') && input.url.startsWith('http://')) {
                    const newUrl = input.url.replace('http://', 'https://');
                    modifiedInput = new Request(newUrl, input);
                    console.log('🔒 [INLINE-SCRIPT] CORRIGIDO:', newUrl);
                  }

                  return originalFetch.call(this, modifiedInput, init);
                };

                console.log('✅ [INLINE-SCRIPT] Interceptor instalado ANTES de tudo!');
              })();
            `,
          }}
        />
        <meta name="application-name" content="Smith 2.0" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="apple-mobile-web-app-title" content="Smith Portal" />
        <meta name="format-detection" content="telephone=no" />
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="theme-color" content="#3b82f6" />

        <link rel="apple-touch-icon" sizes="152x152" href="/icons/icon-152x152.png" />
        <link rel="apple-touch-icon" sizes="192x192" href="/icons/icon-192x192.png" />
        <link rel="apple-touch-icon" sizes="512x512" href="/icons/icon-512x512.png" />

        <link rel="icon" type="image/png" sizes="192x192" href="/icons/icon-192x192.png" />
        <link rel="icon" type="image/png" sizes="512x512" href="/icons/icon-512x512.png" />
        <link rel="shortcut icon" href="/icons/icon-192x192.png" />
      </head>
      <body className={inter.className}>
        <ClientInit />
        <ClientProviders>
          <LayoutWrapper>
            {children}
          </LayoutWrapper>
        </ClientProviders>
      </body>
    </html>
  );
}
