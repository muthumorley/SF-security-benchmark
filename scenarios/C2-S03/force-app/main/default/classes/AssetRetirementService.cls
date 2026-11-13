public with sharing class AssetRetirementService {
    @AuraEnabled
    public static void retireAsset(Id assetId) {
        if (!Schema.sObjectType.Asset.isDeletable()) {
            throw new AuraHandledException('You do not have permission to delete Asset records.');
        }
        Asset a = [SELECT Id, Name, Status FROM Asset WHERE Id = :assetId WITH USER_MODE];
        delete a;
    }
}
