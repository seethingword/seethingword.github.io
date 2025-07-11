import { defineFunction } from "@aws-amplify/backend";

export const sclb = defineFunction({
  name: "sclb",
  entry: "./handler.ts"
});