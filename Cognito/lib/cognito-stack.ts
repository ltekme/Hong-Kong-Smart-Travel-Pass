import { throws } from 'assert';
import { Duration } from 'aws-cdk-lib';
import * as cdk from 'aws-cdk-lib';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import { Construct } from 'constructs';
import { threadId } from 'worker_threads';

// import console = require('console');

export class CognitoStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const userPool = new cognito.UserPool(this, 'UserPool', {
      userPoolName: "smart-travel-pass",
      selfSignUpEnabled: true,
      signInAliases: {
        email: true,
      },
      signInPolicy: {
        allowedFirstAuthFactors: {
          password: true,
          emailOtp: true,
        }
      }
    });
    const userPoolClient = new cognito.UserPoolClient(this, 'UserPoolClient', {
      userPool: userPool,
      generateSecret: false,
      authFlows: {
        user: true
      },

      authSessionValidity: Duration.minutes(3),
      idTokenValidity: Duration.minutes(5),
      refreshTokenValidity: Duration.minutes(60),
      accessTokenValidity: Duration.minutes(5),

      supportedIdentityProviders: [
        cognito.UserPoolClientIdentityProvider.COGNITO,
      ],

      oAuth: {
        callbackUrls: [
          "http://localhost:8000/api/v2/profile/auth/cognito/callback",
          "http://localhost/auth/callback",
          "http://localhost:3000/auth/callback",
        ],
        scopes: [
          cognito.OAuthScope.OPENID,
          cognito.OAuthScope.EMAIL,
        ]
      },
    });
    new cognito.CfnUserPoolDomain(this, "UserPoolClientDomain", {
      userPoolId: userPool.userPoolId,
      managedLoginVersion: 2,
      domain: "smart-travel-pass"
    })

    new cognito.CfnManagedLoginBranding(this, "UserPoolClientManagedLoginStyle", {
      userPoolId: userPool.userPoolId,
      clientId: userPoolClient.userPoolClientId,
      useCognitoProvidedValues: true,
    })

    new cdk.CfnOutput(this, "UserPoolID", {
      value: userPool.userPoolId
    });
    new cdk.CfnOutput(this, "ClientID", {
      value: userPoolClient.userPoolClientId
    });
  }
}
