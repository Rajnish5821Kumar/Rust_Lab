/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Optional absolute API origin. Leave unset to use the same origin (Vite proxy / nginx). */
  readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
