import { betterAuth } from "better-auth";
import { drizzleAdapter } from "better-auth/adapters/drizzle";
import { db } from "#server/db"; // your drizzle instance
import { passkey } from "@better-auth/passkey"
import { admin } from "better-auth/plugins"
import { openAPI } from "better-auth/plugins"
import { expo } from "@better-auth/expo"
import { authSchema } from "../db/schema";

export const auth = betterAuth({
  // advanced: {
  //   database: {
  //     generateId: (options) => {
  //       if (options.model === "passkey") {
  //         return false; // Let the DB handle UUID generation
  //       }
  //       return crypto.randomUUID(); // UUIDs for other tables
  //     },
  //   },
  // },
  database: drizzleAdapter(db, {
    provider: "pg", // or "mysql", "sqlite"
    schema: authSchema
  }),
  emailAndPassword: {
    enabled: true,
  },
  plugins: [
    passkey(),
    admin({
      adminRoles: ['admin']
    }),
    openAPI(),
    expo(),
  ],
  trustedOrigins: [
    "ownit://",
    "exp://",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
  ].concat(process.env.HOMEBASE_TRUSTED_ORIGINS ? process.env.HOMEBASE_TRUSTED_ORIGINS.split(",") : []),
});
