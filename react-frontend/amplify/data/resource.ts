import { type ClientSchema, a, defineData } from '@aws-amplify/backend';

/*== Amplify Gen 2 Data Resource Schema =====================================
 * This schema defines the data models for the Financial Research system.
 * Models:
 *  - Company: Stock metadata (ticker, name, exchange, industry)
 *  - PriceData: Daily OHLCV price history & technical indicators (ma20, rsi14)
 *  - PipelineRun: Logs and status from ETL data ingestion pipelines
 *  - UserPreference: User settings and saved watchlists
 * =========================================================================*/

const schema = a.schema({
  // Company metadata model
  Company: a
    .model({
      ticker: a.string().required(),
      name: a.string().required(),
      exchange: a.string(),
      industry: a.string(),
    })
    .authorization((allow) => [
      allow.guest().to(['read']),
      allow.authenticated().to(['read', 'create', 'update', 'delete']),
    ]),

  // OHLCV Price data & technical indicators model
  PriceData: a
    .model({
      ticker: a.string().required(),
      tradingDate: a.string().required(),
      openPrice: a.float(),
      highPrice: a.float(),
      lowPrice: a.float(),
      closePrice: a.float(),
      volume: a.integer(),
      ma20: a.float(),
      rsi14: a.float(),
    })
    .authorization((allow) => [
      allow.guest().to(['read']),
      allow.authenticated().to(['read', 'create', 'update', 'delete']),
    ]),

  // Pipeline execution log model
  PipelineRun: a
    .model({
      runId: a.string().required(),
      status: a.string().required(),
      requested: a.integer(),
      passed: a.integer(),
      failed: a.integer(),
      rawPath: a.string(),
      message: a.string(),
    })
    .authorization((allow) => [
      allow.guest().to(['read']),
      allow.authenticated().to(['read', 'create', 'update', 'delete']),
    ]),

  // User settings and watchlists
  UserPreference: a
    .model({
      watchlist: a.string().array(),
      theme: a.string(),
      defaultInterval: a.string(),
    })
    .authorization((allow) => [
      allow.owner(),
      allow.authenticated().to(['read', 'create', 'update', 'delete']),
    ]),
});

export type Schema = ClientSchema<typeof schema>;

export const data = defineData({
  schema,
  authorizationModes: {
    defaultAuthorizationMode: 'identityPool',
    apiKeyAuthorizationMode: {
      expiresInDays: 30,
    },
  },
});

