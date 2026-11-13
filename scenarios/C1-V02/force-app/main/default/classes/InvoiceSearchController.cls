public with sharing class InvoiceSearchController {
    @AuraEnabled(cacheable=true)
    public static List<Invoice__c> searchInvoices(String invoiceNum) {
        // VULNERABLE: invoiceNum is concatenated into the SOSL search term
        String searchTerm = 'Invoice-' + invoiceNum;
        List<List<SObject>> results = [FIND :searchTerm IN ALL FIELDS
            RETURNING Invoice__c(Id, Name, Amount__c, Status__c)];
        return (List<Invoice__c>) results[0];
    }
}
