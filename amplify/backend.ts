import { defineBackend } from '@aws-amplify/backend';
import * as apprunner from 'aws-cdk-lib/aws_apprunner';
import * as assets from 'aws-cdk-lib/aws_ecr_assets';
import * as path from 'path';

const backend = defineBackend({});

// 1. Tạo Stack chứa hạ tầng Container
const customStack = backend.createStack('FinancialAppStack');

// 2. Đóng gói Dockerfile của dự án thành ECR Asset
const imageAsset = new assets.DockerImageAsset(customStack, 'FinancialAppImage', {
  directory: path.join(__dirname, '../'), // Chỉ tới thư mục gốc chứa Dockerfile
});

// 3. Tạo AWS App Runner Service chạy Docker Container
new apprunner.CfnService(customStack, 'FinancialAppService', {
  serviceName: 'financial-research-app',
  sourceConfiguration: {
    authenticationConfiguration: {},
    imageRepository: {
      imageIdentifier: imageAsset.imageUri,
      imageRepositoryType: 'ECR',
      imageConfiguration: {
        port: '8501', // Cổng chạy Streamlit
      },
    },
  },
});