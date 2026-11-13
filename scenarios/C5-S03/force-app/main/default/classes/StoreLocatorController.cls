public with sharing class StoreLocatorController {
    @AuraEnabled(cacheable=true)
    public static List<Store__c> getNearbyStores(String city) {
        // Only public fields selected — Internal_Notes__c is intentionally excluded
        return [SELECT Id, Name__c, Street__c, City__c, Phone__c, Opening_Hours__c
                FROM Store__c
                WHERE City__c = :city
                AND Is_Active__c = true
                WITH USER_MODE LIMIT 50];
    }
}
