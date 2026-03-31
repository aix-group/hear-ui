/**
 * E2E Tests: Error Scenarios
 *
 * Tests that the application handles error conditions gracefully:
 * - Invalid API requests return proper error codes
 * - Missing resources return 404
 * - Invalid input returns 422
 */

import { test, expect } from "@playwright/test"

const API_URL = process.env.API_URL || "http://localhost:8000"

test.describe("API Error Handling", () => {
  test("non-existent patient returns 404", async ({ request }) => {
    const response = await request.get(
      `${API_URL}/api/v1/patients/00000000-0000-0000-0000-000000000000`,
    )
    expect(response.status()).toBe(404)
  })

  test("invalid UUID returns 422", async ({ request }) => {
    const response = await request.get(
      `${API_URL}/api/v1/patients/not-a-uuid`,
    )
    expect(response.status()).toBe(422)
  })

  test("empty patient creation returns 422 or 400", async ({ request }) => {
    const response = await request.post(`${API_URL}/api/v1/patients/`, {
      data: { input_features: {} },
    })
    expect([400, 422]).toContain(response.status())
  })

  test("predict with empty body returns 422", async ({ request }) => {
    const response = await request.post(`${API_URL}/api/v1/predict/`, {
      data: {},
    })
    expect(response.status()).toBe(422)
  })

  test("non-existent feedback returns 404", async ({ request }) => {
    const response = await request.get(
      `${API_URL}/api/v1/feedback/00000000-0000-0000-0000-000000000000`,
    )
    expect(response.status()).toBe(404)
  })

  test("batch upload with invalid file type returns 400", async ({
    request,
  }) => {
    const response = await request.post(
      `${API_URL}/api/v1/batch/upload`,
      {
        multipart: {
          file: {
            name: "test.txt",
            mimeType: "text/plain",
            buffer: Buffer.from("not,a,valid,csv\n"),
          },
        },
      },
    )
    // Accepts 400 (invalid type) or 422 (validation) or similar client error
    expect(response.status()).toBeGreaterThanOrEqual(400)
    expect(response.status()).toBeLessThan(500)
  })

  test("non-existent route returns 404", async ({ request }) => {
    const response = await request.get(
      `${API_URL}/api/v1/does-not-exist`,
    )
    expect(response.status()).toBe(404)
  })
})
