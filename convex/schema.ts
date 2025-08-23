import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

const RelationshipType = v.union(
  v.literal("friend"),
  v.literal("family"),
  v.literal("romantic"),
  v.literal("colleague"),
  v.literal("acquaintance")
);

const ActionType = v.union(
  v.literal("message"),
  v.literal("gift"),
  v.literal("flowers"),
  v.literal("restaurant"),
  v.literal("experience"),
  v.literal("donation"),
  v.literal("service")
);

export default defineSchema({
  logs: defineTable({
    timestamp: v.number(),
    version: v.string(),
    context: v.object({
      situation: v.string(),
      recipient_name: v.string(),
      relationship_type: RelationshipType,
      severity: v.number(),
      recipient_preferences: v.any(),
      budget: v.optional(v.number()),
      location: v.optional(v.string()),
    }),
    response: v.object({
      apology_message: v.string(),
      strategy_explanation: v.string(),
      recommended_actions: v.array(
        v.object({
          type: ActionType,
          description: v.string(),
          estimated_cost: v.optional(v.number()),
          execution_details: v.any(),
          priority: v.number(),
        })
      ),
      estimated_total_cost: v.optional(v.number()),
      success_probability: v.number(),
      follow_up_suggestions: v.array(v.string()),
    }),
  }).index("by_timestamp", ["timestamp"]),

  reservations: defineTable({
    timestamp: v.number(),
    version: v.string(),
    context: v.object({
      situation: v.string(),
      recipient_name: v.string(),
      relationship_type: RelationshipType,
      severity: v.number(),
      recipient_preferences: v.any(),
      budget: v.optional(v.number()),
      location: v.optional(v.string()),
    }),
    response: v.object({
      apology_message: v.string(),
      strategy_explanation: v.string(),
      recommended_actions: v.array(
        v.object({
          type: ActionType,
          description: v.string(),
          estimated_cost: v.optional(v.number()),
          execution_details: v.any(),
          priority: v.number(),
        })
      ),
      estimated_total_cost: v.optional(v.number()),
      success_probability: v.number(),
      follow_up_suggestions: v.array(v.string()),
    }),
  }).index("by_timestamp", ["timestamp"]),
});
