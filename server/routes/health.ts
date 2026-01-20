import { db } from "#server/db"

export default defineEventHandler(async (event) => {
  // db health check
  let dbCheck = true
  try {
    await db.execute(`SELECT 1`)
  } catch (e) {
    dbCheck = false
  }

  const all_checks: boolean[] = [dbCheck]
  let statusText = "ok"

  if (all_checks.every(v => v)) {
    setResponseStatus(event, 200)
  } else {
    setResponseStatus(event, 503)
    statusText = "error"
  }

  return {
    status: all_checks.every(v => v) ? "ok" : "error",
    services: {
      database: dbCheck ? "ok" : "error",
    }
  }
})
