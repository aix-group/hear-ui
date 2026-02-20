/**
 * E2E Tests: Feedback Workflow
 * 
 * Tests:
 * 1. POST /feedback/ - Create feedback
 * 2. GET /feedback/{id} - Read feedback
 * 3. Validation of feedback persistence
 */

import { test, expect } from '@playwright/test';

const API_URL = process.env.API_URL || 'http://localhost:8000';

test.describe('Feedback API', () => {
  // feedbackId is captured in the first test but consumed only for local verification
  let _feedbackId: string;

  test('create feedback returns valid response', async ({ request }) => {
    const response = await request.post(`${API_URL}/api/v1/feedback/`, {
      data: {
        input_features: { 'Alter [J]': 55, 'Geschlecht': 'w' },
        prediction: 0.85,
        accepted: true,
        comment: 'E2E Test Feedback'
      }
    });
    
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    
    // Verify response structure
    expect(data).toHaveProperty('id');
    expect(data).toHaveProperty('input_features');
    expect(data).toHaveProperty('prediction');
    expect(data).toHaveProperty('accepted');
    expect(data).toHaveProperty('created_at');
    
    // Store ID for reference (verified below)
    _feedbackId = data.id;
    
    // Verify values
    expect(data.prediction).toBe(0.85);
    expect(data.accepted).toBe(true);
  });

  test('read feedback by id', async ({ request }) => {
    // First create a feedback to ensure we have one
    const createResponse = await request.post(`${API_URL}/api/v1/feedback/`, {
      data: {
        input_features: { age: 45 },
        prediction: 0.72,
        accepted: false
      }
    });
    
    expect(createResponse.ok()).toBeTruthy();
    const created = await createResponse.json();
    
    // Now read it back
    const readResponse = await request.get(`${API_URL}/api/v1/feedback/${created.id}`);
    
    expect(readResponse.ok()).toBeTruthy();
    const data = await readResponse.json();
    
    expect(data.id).toBe(created.id);
    expect(data.prediction).toBe(0.72);
    expect(data.accepted).toBe(false);
  });

  test('feedback with all optional fields', async ({ request }) => {
    const response = await request.post(`${API_URL}/api/v1/feedback/`, {
      data: {
        input_features: {
          'Alter [J]': 60,
          'Geschlecht': 'm',
          'Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)...': '5-10 y'
        },
        prediction: 0.65,
        accepted: true,
        comment: 'Detailed feedback with all fields',
        explanation: {
          top_feature: 'Alter [J]',
          importance: 0.15
        }
      }
    });
    
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    
    expect(data.comment).toBe('Detailed feedback with all fields');
  });

  test('feedback for non-existent id returns 404', async ({ request }) => {
    const fakeId = '00000000-0000-0000-0000-000000000000';
    const response = await request.get(`${API_URL}/api/v1/feedback/${fakeId}`);
    
    expect(response.status()).toBe(404);
  });
});
