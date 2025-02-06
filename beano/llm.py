
from typing import List

import boto3


class ModelRegionLister:
    def __init__(self, region):
        """Initialize with AWS region"""
        self.region = region
        self.bedrock_client = boto3.client('bedrock', region_name=region)

    def list_enabled_models(self, model_ids: List[str]):
        """List all enabled model IDs in the region"""
        try:
            # Get list of foundation models
            response = self.bedrock_client.list_foundation_models()

            # Filter for enabled models only
            enabled_models = [
                (model['modelId'], model['modelName'])
                for model in response['modelSummaries']
                if model['modelId'] in model_ids
                # if model['modelLifecycle']['status'] == 'ACTIVE'
            ]

            return enabled_models

        except Exception as e:
            print(f"Error listing models in region {self.region}: {str(e)}")
            return []


def get_model_pricing(modelName, region):
    """Get pricing information for a Bedrock model in the specified region

    Args:
        model_id (str): The Bedrock model ID to get pricing for

    Returns:
        dict: Dictionary containing pricing information, or None if not found
    """
    try:
        # Create pricing client
        pricing_client = boto3.client('pricing', region_name='us-east-1')

        # Get pricing for the specified model
        response = pricing_client.get_products(
            ServiceCode='AmazonBedrock',
            Filters=[
                {
                    'Type': 'TERM_MATCH',
                    'Field': 'model',
                    'Value': modelName
                },
                # {
                #     'Type': 'TERM_MATCH',
                #     'Field': 'regionCode',
                #     'Value': region
                # }
            ]
        )

        if len(response['PriceList']) > 0:
            # Parse and return the pricing data
            pricing_data = response['PriceList']
            return pricing_data
        else:
            print(f"No pricing found for model {
                  modelName} in region {region}")
            return None

    except Exception as e:
        print(f"Error getting pricing for model {modelName}: {str(e)}")
        return None


def main():
    """Test the ModelRegionLister class"""
    # Create instance for us-east-1 region
    region = 'us-east-1'
    lister = ModelRegionLister(region)

    # Get enabled models
    enabled_models = lister.list_enabled_models(
        ['amazon.nova-lite-v1:0', 'anthropic.claude-3-5-haiku-20241022-v1:0'])

    # Print results
    print(f"Enabled models in us-east-1:")
    for modelId, modelName in enabled_models:
        print(f"- {modelId} - {get_model_pricing(modelName, region)}")


if __name__ == "__main__":
    main()
    # pricing_client = boto3.client('pricing', region_name='us-east-1')

    # # Get pricing for the specified model
    # response = pricing_client.get_products(
    #     ServiceCode='AmazonBedrock',
    #                 Filters=[

    #                     {
    #                         'Type': 'TERM_MATCH',
    #                         'Field': 'regionCode',
    #                         'Value': 'us-east-1'
    #                     }
    #                 ])

    # print(response)
