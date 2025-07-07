#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { CognitoStack } from '../lib/cognito-stack';

const app = new cdk.App();
const stack = new CognitoStack(app, 'CognitoStack', {});

new cdk.CfnOutput(stack, "Region", {
  value: new cdk.Stack(stack).region
})