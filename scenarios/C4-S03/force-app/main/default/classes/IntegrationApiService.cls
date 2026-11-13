public with sharing class IntegrationApiService {
    @AuraEnabled(cacheable=true)
    public static List<Order> getOrdersForSync(String externalSystemId) {
        return [SELECT Id, OrderNumber, Status, TotalAmount, ExternalId__c
                FROM Order
                WHERE ExternalId__c = :externalSystemId
                WITH USER_MODE LIMIT 500];
    }

    @AuraEnabled
    public static void updateSyncStatus(Id orderId, String syncStatus) {
        Order o = new Order(Id = orderId, Sync_Status__c = syncStatus);
        update as user o;
    }
}
