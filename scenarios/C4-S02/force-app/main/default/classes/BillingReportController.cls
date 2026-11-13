public with sharing class BillingReportController {
    @AuraEnabled(cacheable=true)
    public static List<Order> getBillingOrders(String statusFilter) {
        return [SELECT Id, OrderNumber, Status, TotalAmount, BillingCity
                FROM Order
                WHERE Status = :statusFilter
                WITH USER_MODE LIMIT 200];
    }
}
