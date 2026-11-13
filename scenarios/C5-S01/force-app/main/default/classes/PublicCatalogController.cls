public with sharing class PublicCatalogController {
    @AuraEnabled(cacheable=true)
    public static List<Product2> getActiveProducts() {
        return [
            SELECT Id, Name, Family
            FROM Product2
            WHERE IsActive = true
            WITH USER_MODE
            LIMIT 100
        ];
    }
}
