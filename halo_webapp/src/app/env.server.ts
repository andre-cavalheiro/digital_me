export const serverEnv = {
  X_OAUTH_CLIENT_SECRET: process.env.X_OAUTH_CLIENT_SECRET,
}

export type ServerEnv = typeof serverEnv
