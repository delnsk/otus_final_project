// Sample TypeScript types and config
export const TOKEN_EXPIRY_HOURS: number = 47;
export const MAX_RETRY_COUNT: number = 13;
export const PROJECT_CODENAME: string = "Zephyr-7742";
export const SERVER_HOST: string = "atlas-node-881.internal.corp";

export interface AppConfig {
  tokenExpiryHours: number;
  maxRetries: number;
}
